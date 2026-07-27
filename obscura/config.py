import json
import os
import platform
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional


CONFIG_VERSION = 1
DEFAULT_CATEGORIES = {
    "email",
    "base64_key",
    "endpoint",
    "phone",
    "iban",
    "mac",
    "ssn_fr",
    "jwt",
    "api_key",
    "github_token",
    "aws_key",
    "credit_card",
    "credential",
    "private_key",
}


def data_directory() -> Path:
    system = platform.system()
    if system == "Windows":
        root = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif system == "Darwin":
        root = Path.home() / "Library" / "Application Support"
    else:
        root = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return root / "Obscura"


@dataclass
class CustomRule:
    name: str
    value: str
    is_regex: bool = False
    enabled: bool = True

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "CustomRule":
        return cls(
            name=str(value.get("name", "Custom rule")),
            value=str(value.get("value", "")),
            is_regex=bool(value.get("is_regex", False)),
            enabled=bool(value.get("enabled", True)),
        )


@dataclass
class AppConfig:
    version: int = CONFIG_VERSION
    language: str = "fr"
    clipboard_enabled: bool = True
    clipboard_interval: float = 0.5
    watch_directory_enabled: bool = False
    watch_directory: str = ""
    output_directory: str = ""
    recursive_watch: bool = True
    replace_source: bool = False
    output_suffix: str = "-obscura"
    output_extensions: list[str] = field(default_factory=lambda: [".png", ".jpg", ".jpeg", ".webp"])
    copy_file_output_to_clipboard: bool = False
    active_categories: set[str] = field(default_factory=lambda: set(DEFAULT_CATEGORIES))
    custom_rules: list[CustomRule] = field(default_factory=list)
    ocr_languages: list[str] = field(default_factory=lambda: ["fra", "eng"])
    ocr_confidence: int = 10
    redaction_mode: str = "blur"
    blur_radius: int = 15
    pixel_size: int = 12
    notifications_enabled: bool = True
    critical_update_notifications: bool = True
    face_detection_enabled: bool = False
    name_detection_enabled: bool = False
    autostart_enabled: bool = False
    update_check_interval_hours: int = 24

    def normalize(self) -> None:
        self.version = CONFIG_VERSION
        self.language = self.language if self.language in {"fr", "en"} else "fr"
        self.clipboard_interval = min(10.0, max(0.1, float(self.clipboard_interval)))
        self.ocr_confidence = min(100, max(0, int(self.ocr_confidence)))
        self.blur_radius = min(100, max(1, int(self.blur_radius)))
        self.pixel_size = min(100, max(2, int(self.pixel_size)))
        self.redaction_mode = self.redaction_mode if self.redaction_mode in {"black", "blur", "pixelate"} else "blur"
        self.output_suffix = self.output_suffix.strip() or "-obscura"
        if not self.output_suffix.startswith(("-", "_")):
            self.output_suffix = f"-{self.output_suffix}"
        self.output_extensions = sorted({ext.lower() if ext.startswith(".") else f".{ext.lower()}" for ext in self.output_extensions})
        self.ocr_languages = [lang for lang in self.ocr_languages if lang in {"fra", "eng"}] or ["eng"]
        self.active_categories = set(self.active_categories) & DEFAULT_CATEGORIES
        self.update_check_interval_hours = min(168, max(1, int(self.update_check_interval_hours)))

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["active_categories"] = sorted(self.active_categories)
        return payload

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AppConfig":
        fields = cls.__dataclass_fields__
        values = {key: value for key, value in data.items() if key in fields}
        values["active_categories"] = set(values.get("active_categories", DEFAULT_CATEGORIES))
        values["custom_rules"] = [CustomRule.from_dict(item) for item in values.get("custom_rules", []) if isinstance(item, dict)]
        config = cls(**values)
        config.normalize()
        return config


def config_path() -> Path:
    return data_directory() / "config.json"


def load_config(path: Optional[Path] = None) -> AppConfig:
    target = path or config_path()
    try:
        with target.open(encoding="utf-8") as handle:
            payload = json.load(handle)
        if not isinstance(payload, dict):
            raise ValueError("Configuration must be an object")
        return AppConfig.from_dict(payload)
    except (FileNotFoundError, OSError, ValueError, json.JSONDecodeError):
        return AppConfig()


def save_config(config: AppConfig, path: Optional[Path] = None) -> Path:
    config.normalize()
    target = path or config_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(config.to_dict(), handle, ensure_ascii=False, indent=2)
    temporary.replace(target)
    return target
