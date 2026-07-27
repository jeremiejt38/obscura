from pathlib import Path

from PIL import Image

from obscura import autostart
from obscura.config import AppConfig
from obscura.main import process_image


def test_process_image_preserves_explicit_config_mode(monkeypatch):
    observed = {}

    def fake_redact(image, config):
        observed["mode"] = config.redaction_mode
        return type("Result", (), {"image": image, "count": 0})()

    monkeypatch.setattr("obscura.main.redact", fake_redact)

    process_image(Image.new("RGB", (1, 1), "white"), mode="blur", config=AppConfig(redaction_mode="black"))

    assert observed["mode"] == "black"


def test_macos_autostart_uses_separate_program_arguments(monkeypatch, tmp_path):
    target = tmp_path / "com.obscura.app.plist"
    monkeypatch.setattr(autostart.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(autostart, "_target", lambda: target)
    monkeypatch.setattr(autostart, "_command_parts", lambda: ["/Applications/Obscura & Co", "--tray"])

    autostart.set_enabled(True)

    content = target.read_text(encoding="utf-8")
    assert "<array><string>/Applications/Obscura &amp; Co</string><string>--tray</string></array>" in content
    assert "<string>/Applications/Obscura &amp; Co --tray</string>" not in content


def test_update_check_is_not_started_automatically():
    source = Path("obscura/desktop.py").read_text(encoding="utf-8")

    assert "QTimer.singleShot" not in source
