import os
import time
from pathlib import Path
from typing import Callable
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class ScreenshotHandler(FileSystemEventHandler):
    def __init__(
        self,
        callback: Callable[[str], None],
        extensions: tuple = (".png", ".jpg", ".jpeg"),
        ignored_stem_suffix: str = "_redacted",
    ):
        self.callback = callback
        self.extensions = extensions
        self.ignored_stem_suffix = ignored_stem_suffix
        self._seen: set = set()

    def on_created(self, event):
        if event.is_directory:
            return
        path = event.src_path
        if self._should_process(path):
            self._process(path)

    def on_modified(self, event):
        if event.is_directory:
            return
        path = event.src_path
        if self._should_process(path):
            self._process(path)

    def _should_process(self, path: str) -> bool:
        return path.lower().endswith(self.extensions) and not Path(path).stem.endswith(self.ignored_stem_suffix)

    def _process(self, path: str):
        # Debounce: wait until the file stops growing.
        if path in self._seen:
            return
        self._seen.add(path)
        try:
            size_before = -1
            for _ in range(20):
                size_after = os.path.getsize(path)
                if size_after == size_before and size_after > 0:
                    break
                size_before = size_after
                time.sleep(0.1)
            self.callback(path)
        finally:
            self._seen.discard(path)


def watch_directory(
    directory: str,
    callback: Callable[[str], None],
    ignored_stem_suffix: str = "_redacted",
) -> None:
    handler = ScreenshotHandler(callback, ignored_stem_suffix=ignored_stem_suffix)
    observer = Observer()
    observer.schedule(handler, directory, recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
