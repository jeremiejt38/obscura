import os
import platform
import shlex
import sys
from pathlib import Path
from xml.sax.saxutils import escape


APP_NAME = "Obscura"


def _command_parts() -> list[str]:
    executable = Path(sys.argv[0]).resolve()
    if getattr(sys, "frozen", False):
        return [str(executable)]
    return [sys.executable, "-m", "obscura.desktop"]


def _command() -> str:
    return shlex.join(_command_parts())


def _target() -> Path:
    system = platform.system()
    if system == "Windows":
        return Path(os.environ["APPDATA"]) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup" / f"{APP_NAME}.cmd"
    if system == "Darwin":
        return Path.home() / "Library" / "LaunchAgents" / "com.obscura.app.plist"
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "autostart" / "obscura.desktop"


def is_enabled() -> bool:
    return _target().exists()


def set_enabled(enabled: bool) -> None:
    target = _target()
    if not enabled:
        target.unlink(missing_ok=True)
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    command = _command()
    system = platform.system()
    if system == "Windows":
        target.write_text(f"@echo off\nstart \"\" {command}\n", encoding="utf-8")
    elif system == "Darwin":
        arguments = "".join(f"<string>{escape(argument)}</string>" for argument in _command_parts())
        target.write_text(
            "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
            "<!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" \"http://www.apple.com/DTDs/PropertyList-1.0.dtd\">\n"
            "<plist version=\"1.0\"><dict><key>Label</key><string>com.obscura.app</string>"
            f"<key>ProgramArguments</key><array>{arguments}</array>"
            "<key>RunAtLoad</key><true/></dict></plist>\n",
            encoding="utf-8",
        )
    else:
        target.write_text(f"[Desktop Entry]\nType=Application\nName={APP_NAME}\nExec={command}\nX-GNOME-Autostart-enabled=true\n", encoding="utf-8")
