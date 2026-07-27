from pathlib import Path
from types import SimpleNamespace

from PIL import Image

from obscura.config import AppConfig, CustomRule, load_config, save_config
from obscura.main import process_image
from obscura.engine import redact
from obscura.redactor import Box
from obscura.service import output_path


def word(text, x, y, width, height):
    return {"text": text, "box": Box(x, y, width, height), "line": (1, 1, 1, 1), "left": x}


def test_configuration_round_trip(tmp_path):
    path = tmp_path / "config.json"
    config = AppConfig(redaction_mode="pixelate", active_categories={"email"}, custom_rules=[CustomRule("Internal", "acme")])

    save_config(config, path)
    loaded = load_config(path)

    assert loaded.redaction_mode == "pixelate"
    assert loaded.active_categories == {"email"}
    assert loaded.custom_rules[0].value == "acme"


def test_default_redaction_mode_is_blur():
    assert AppConfig().redaction_mode == "blur"
    config = AppConfig(redaction_mode="unknown")

    config.normalize()

    assert config.redaction_mode == "blur"


def test_process_image_defaults_to_blur(monkeypatch):
    observed = {}

    def fake_redact(image, config):
        observed["mode"] = config.redaction_mode
        return SimpleNamespace(image=image, count=0)

    monkeypatch.setattr("obscura.main.redact", fake_redact)

    process_image(Image.new("RGB", (1, 1), "white"))

    assert observed["mode"] == "blur"


def test_default_configuration_excludes_ipv4(monkeypatch):
    monkeypatch.setattr("obscura.engine.extract_words", lambda *_args, **_kwargs: [word("192.168.1.10", 5, 5, 30, 10)])

    result = redact(Image.new("RGB", (50, 30), "white"), AppConfig())

    assert result.count == 0


def test_engine_honors_active_categories(monkeypatch):
    monkeypatch.setattr("obscura.engine.extract_words", lambda *_args, **_kwargs: [word("user@example.com", 5, 5, 30, 10)])
    config = AppConfig(active_categories=set())

    result = redact(Image.new("RGB", (50, 30), "white"), config)

    assert result.count == 0


def test_engine_pixelates_custom_rule(monkeypatch):
    monkeypatch.setattr("obscura.engine.extract_words", lambda *_args, **_kwargs: [word("internal", 5, 5, 30, 10)])
    config = AppConfig(active_categories=set(), custom_rules=[CustomRule("Internal", "internal")], redaction_mode="pixelate", pixel_size=4)

    result = redact(Image.new("RGB", (50, 30), "white"), config)

    assert result.count == 1


def test_output_path_preserves_relative_directory(tmp_path):
    source_root = tmp_path / "input"
    source = source_root / "nested" / "capture.png"
    config = AppConfig(output_directory=str(tmp_path / "output"))

    assert output_path(source, config, source_root) == tmp_path / "output" / "nested" / "capture-obscura.png"
