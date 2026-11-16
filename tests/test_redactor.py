import pytest
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


class TestNewPatterns:
    @pytest.mark.parametrize("text", [
        "Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.abc.def",
        "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIMock1234 user@host",
        "server at 203.0.113.7 is down",
        "https://discord.com/api/webhooks/123/abc",
        "IBAN: FR1420041010050500013M02606",
        "contact au 06 12 34 56 78",
        "card 4111 1111 1111 1111",
        "key sk-AbCdEf1234567890",
        "-----BEGIN PRIVATE KEY-----",
    ])
    def test_detects_new_categories(self, text):
        from obscura.redactor import SENSITIVE_PATTERNS
        assert any(p.search(text) for p, _ in SENSITIVE_PATTERNS)

    def test_no_false_positive_on_plain_text(self):
        from obscura.redactor import SENSITIVE_PATTERNS
        assert not any(p.search("The quick brown fox 1.2 is fine") for p, _ in SENSITIVE_PATTERNS)


class TestExtendedPatterns:
    @pytest.mark.parametrize("text", [
        "token github_pat_11ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
        "gitlab glpat-AbCdEfGhIjKlMnOpQrSt",
        "slack xoxb-1234567890-abcdefghij",
        "hf_AbCdEfGhIjKlMnOpQrStUvWxYz0123",
        "stripe " + "sk" + "_live_" + "0" * 20,
        "google " + "AI" + "za" + "0" * 35,
        "host 2001:0db8:85a3:0000:0000:8a2e:0370:7334 up",
        "host ::1 loopback",
        "url https://admin:s3cret@example.com/path",
    ])
    def test_detects_extended_patterns(self, text):
        from obscura.redactor import SENSITIVE_PATTERNS
        assert any(p.search(text) for p, _ in SENSITIVE_PATTERNS), text

    def test_luhn_rejects_invalid_card(self):
        boxes = find_sensitive_boxes([word("card", 0, 0, 40, 10), word("1234567890123456", 50, 0, 160, 10)])
        assert not any(getattr(b, "label", "") == "credit_card" for b in boxes)

    def test_luhn_accepts_valid_card(self):
        boxes = find_sensitive_boxes([word("card", 0, 0, 40, 10), word("4539578763621486", 50, 0, 160, 10)])
        assert len(boxes) >= 1


class TestCustomRules:
    def test_literal_rule_compiles(self):
        from obscura.config import AppConfig, CustomRule
        from obscura.engine import _patterns
        config = AppConfig(custom_rules=[CustomRule(name="internal", value="internal.example.invalid")])
        labels = [label for _, label in _patterns(config)]
        assert "custom:internal" in labels

    def test_regex_rule_compiles(self):
        import re
        from obscura.config import AppConfig, CustomRule
        from obscura.engine import _patterns
        config = AppConfig(custom_rules=[CustomRule(name="dom", value=r"\.internal\.lan$", is_regex=True)])
        patterns = _patterns(config)
        pattern, label = next(item for item in patterns if item[1] == "custom:dom")
        assert pattern.search("host.internal.lan")

    def test_disabled_rule_skipped(self):
        from obscura.config import AppConfig, CustomRule
        from obscura.engine import _patterns
        config = AppConfig(custom_rules=[CustomRule(name="off", value="x", enabled=False)])
        assert not any(label == "custom:off" for _, label in _patterns(config))

    def test_invalid_regex_skipped(self):
        from obscura.config import AppConfig, CustomRule
        from obscura.engine import _patterns
        config = AppConfig(custom_rules=[CustomRule(name="bad", value="[", is_regex=True)])
        assert not any(label == "custom:bad" for _, label in _patterns(config))
