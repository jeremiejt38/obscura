from PIL import Image

from obscura.redactor import Box, find_sensitive_boxes, merge_overlapping_boxes, redact_image


def word(text, x, y, width, height):
    return {"text": text, "box": Box(x, y, width, height), "line": (1, 1, 1, 1), "left": x}


def test_detects_email_across_words():
    boxes = find_sensitive_boxes([word("contact", 0, 0, 50, 10), word("user@example.com", 60, 0, 120, 10)])

    assert len(boxes) == 1
    assert boxes[0].to_tuple() == (60, 0, 180, 10)


def test_merges_overlapping_boxes():
    merged = merge_overlapping_boxes([Box(10, 10, 20, 10), Box(25, 10, 20, 10)], margin=0)

    assert merged == [Box(10, 10, 35, 10)]


def test_redact_image_applies_black_mask(monkeypatch):
    monkeypatch.setattr("obscura.redactor.extract_words", lambda image: [word("user@example.com", 5, 5, 30, 10)])
    image, count = redact_image(Image.new("RGB", (50, 30), "white"))

    assert count == 1
    assert image.getpixel((10, 10)) == (0, 0, 0)
