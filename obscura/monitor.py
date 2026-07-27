import threading
import time
from pathlib import Path
from typing import Callable, Optional

from PIL import Image
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from .config import AppConfig
from .engine import RedactionResult, redact
from .service import output_path


class ClipboardMonitor:
    def __init__(self, config: AppConfig, on_result: Callable[[RedactionResult], None], on_error: Callable[[Exception], None]):
        self.config = config
        self.on_result = on_result
        self.on_error = on_error
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._last_digest = ""

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="obscura-clipboard", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=3)

    def _run(self) -> None:
        from .clipboard import read_image_from_clipboard, write_image_to_clipboard

        while not self._stop.is_set():
            try:
                image, digest = read_image_from_clipboard()
                if image is not None and digest and digest != self._last_digest:
                    result = redact(image, self.config)
                    if result.count:
                        self._last_digest = write_image_to_clipboard(result.image)
                        self.on_result(result)
                    else:
                        self._last_digest = digest
            except Exception as exc:
                self.on_error(exc)
            self._stop.wait(self.config.clipboard_interval)


class _DirectoryHandler(FileSystemEventHandler):
    def __init__(self, monitor: "DirectoryMonitor"):
        self.monitor = monitor

    def on_created(self, event) -> None:
        self.monitor.submit(event)

    def on_modified(self, event) -> None:
        self.monitor.submit(event)


class DirectoryMonitor:
    def __init__(self, config: AppConfig, on_result: Callable[[RedactionResult], None], on_error: Callable[[Exception], None]):
        self.config = config
        self.on_result = on_result
        self.on_error = on_error
        self._observer: Optional[Observer] = None
        self._seen: set[str] = set()
        self._lock = threading.Lock()

    def start(self) -> None:
        source = Path(self.config.watch_directory).expanduser()
        if self._observer or not source.is_dir():
            return
        self._observer = Observer()
        self._observer.schedule(_DirectoryHandler(self), str(source), recursive=self.config.recursive_watch)
        self._observer.start()

    def stop(self) -> None:
        if self._observer:
            self._observer.stop()
            self._observer.join(timeout=3)
            self._observer = None

    def submit(self, event) -> None:
        if event.is_directory:
            return
        path = Path(event.src_path)
        if path.suffix.lower() not in self.config.output_extensions or path.stem.endswith(self.config.output_suffix):
            return
        with self._lock:
            if str(path) in self._seen:
                return
            self._seen.add(str(path))
        threading.Thread(target=self._process, args=(path,), daemon=True).start()

    def _process(self, path: Path) -> None:
        try:
            for _ in range(20):
                before = path.stat().st_size
                time.sleep(0.1)
                if path.stat().st_size == before and before:
                    break
            image = Image.open(path).convert("RGB")
            result = redact(image, self.config)
            if result.count:
                destination = output_path(path, self.config, Path(self.config.watch_directory).expanduser())
                destination.parent.mkdir(parents=True, exist_ok=True)
                result.image.save(destination)
                if self.config.copy_file_output_to_clipboard:
                    from .clipboard import write_image_to_clipboard

                    write_image_to_clipboard(result.image)
                self.on_result(result)
        except Exception as exc:
            self.on_error(exc)
        finally:
            with self._lock:
                self._seen.discard(str(path))
