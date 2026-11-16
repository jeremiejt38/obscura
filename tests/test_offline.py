"""FR-OBS-08: no network socket may be opened while processing an image."""
import socket

import pytest
from PIL import Image

from obscura.redactor import redact_image


def test_redact_image_opens_no_socket(monkeypatch):
    def _forbidden(*args, **kwargs):
        raise AssertionError("network access during image processing")

    monkeypatch.setattr(socket, "socket", _forbidden)
    monkeypatch.setattr(socket, "create_connection", _forbidden)
    monkeypatch.setattr(
        "obscura.redactor.extract_words",
        lambda image: [{"text": "user@example.com", "box": __import__("obscura.redactor", fromlist=["Box"]).Box(0, 0, 10, 5), "line": (1, 1, 1, 1), "left": 0}],
    )
    image, count = redact_image(Image.new("RGB", (30, 20), "white"))
    assert count == 1
