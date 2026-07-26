from obscura.watcher import ScreenshotHandler


def test_ignores_redacted_outputs():
    handler = ScreenshotHandler(lambda path: None)

    assert handler._should_process("/tmp/capture.png")
    assert not handler._should_process("/tmp/capture_redacted.png")
    assert not handler._should_process("/tmp/notes.txt")
