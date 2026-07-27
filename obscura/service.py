import queue
import threading
from pathlib import Path
from typing import Callable, Optional

from PIL import Image

from .config import AppConfig
from .engine import RedactionResult, redact


class ProcessingService:
    def __init__(self, config: AppConfig):
        self.config = config
        self._jobs: queue.Queue[tuple[Image.Image, Callable[[RedactionResult], None], Callable[[Exception], None] | None]] = queue.Queue()
        self._stopped = threading.Event()
        self._thread = threading.Thread(target=self._run, name="obscura-processor", daemon=True)
        self._thread.start()

    def submit(
        self,
        image: Image.Image,
        on_success: Callable[[RedactionResult], None],
        on_error: Callable[[Exception], None] | None = None,
    ) -> None:
        self._jobs.put((image.copy(), on_success, on_error))

    def process(self, image: Image.Image) -> RedactionResult:
        return redact(image, self.config)

    def close(self) -> None:
        self._stopped.set()
        self._jobs.put((Image.new("RGB", (1, 1)), lambda _: None, None))
        self._thread.join(timeout=3)

    def _run(self) -> None:
        while not self._stopped.is_set():
            image, on_success, on_error = self._jobs.get()
            if self._stopped.is_set():
                return
            try:
                on_success(redact(image, self.config))
            except Exception as exc:
                if on_error:
                    on_error(exc)


def output_path(source: Path, config: AppConfig, root: Optional[Path] = None) -> Path:
    if config.replace_source:
        return source
    if config.output_directory:
        destination_root = Path(config.output_directory)
        relative = source.relative_to(root) if root else Path(source.name)
        destination = destination_root / relative.parent
    else:
        destination = source.parent
    return destination / f"{source.stem}{config.output_suffix}{source.suffix}"
