import hashlib
import json
import platform
import shutil
import subprocess
import sys
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from .config import data_directory
from . import __version__


RELEASE_API = "https://api.github.com/repos/jeremiejt38/Obscura/releases/latest"


@dataclass(frozen=True)
class UpdateInfo:
    version: str
    asset_url: str
    checksum_url: str
    critical: bool = False


def _version_tuple(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in version.removeprefix("v").split(".") if part.isdigit())


def _check_state_path() -> Path:
    return data_directory() / "update-check.json"


def _load_cached_update(interval_hours: int) -> Any:
    path = _check_state_path()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if time.time() - float(payload["checked_at"]) >= interval_hours * 3600:
            return _UNCACHED
        update = payload.get("update")
        return UpdateInfo(**update) if update else None
    except (FileNotFoundError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        return _UNCACHED


def _save_cached_update(update: Optional[UpdateInfo]) -> None:
    path = _check_state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"checked_at": time.time(), "update": update.__dict__ if update else None}
    path.write_text(json.dumps(payload), encoding="utf-8")


_UNCACHED = object()


def check_for_update(timeout: int = 5, interval_hours: int = 24, force: bool = False) -> Optional[UpdateInfo]:
    if not force:
        cached = _load_cached_update(interval_hours)
        if cached is not _UNCACHED:
            return cached
    request = urllib.request.Request(RELEASE_API, headers={"Accept": "application/vnd.github+json", "User-Agent": "Obscura"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.load(response)
    version = str(payload.get("tag_name", ""))
    suffix = {"Windows": "windows.exe", "Darwin": "macos", "Linux": "linux"}.get(platform.system())
    update = None
    if version and suffix and _version_tuple(version) > _version_tuple(__version__):
        assets = {asset["name"]: asset["browser_download_url"] for asset in payload.get("assets", [])}
        asset_name = next((name for name in assets if name.endswith(suffix)), None)
        checksum_name = next((name for name in assets if name.endswith(f"{suffix}.sha256")), None)
        if asset_name and checksum_name:
            update = UpdateInfo(version=version, asset_url=assets[asset_name], checksum_url=assets[checksum_name], critical="[critical]" in str(payload.get("body", "")).lower())
    _save_cached_update(update)
    return update


def download_update(update: UpdateInfo, destination: Optional[Path] = None) -> Path:
    destination = destination or data_directory() / "updates" / f"obscura-{update.version}{Path(update.asset_url).suffix}"
    destination.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(update.asset_url, timeout=30) as response, destination.open("wb") as handle:
        shutil.copyfileobj(response, handle)
    with urllib.request.urlopen(update.checksum_url, timeout=10) as response:
        expected = response.read().decode("utf-8").split()[0].lower()
    actual = hashlib.sha256(destination.read_bytes()).hexdigest().lower()
    if actual != expected:
        destination.unlink(missing_ok=True)
        raise RuntimeError("Update integrity verification failed")
    return destination


def install_update(downloaded: Path) -> None:
    if not getattr(sys, "frozen", False):
        raise RuntimeError("In-app updates are available only from packaged releases")
    current = Path(sys.executable).resolve()
    update_dir = data_directory() / "updates"
    update_dir.mkdir(parents=True, exist_ok=True)
    if platform.system() == "Windows":
        helper = update_dir / "replace.cmd"
        helper.write_text(
            "@echo off\r\n"
            "timeout /t 2 /nobreak >nul\r\n"
            "copy /Y %~1 %~2 >nul\r\n"
            "start \"\" %~2\r\n"
            "del %~f0\r\n",
            encoding="utf-8",
        )
        subprocess.Popen(["cmd", "/c", str(helper), str(downloaded), str(current)], creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
        return
    helper = update_dir / "replace.sh"
    helper.write_text(
        "#!/bin/sh\n"
        "sleep 2\n"
        "cp \"$1\" \"$2\".previous\n"
        "mv \"$1\" \"$2\"\n"
        "chmod +x \"$2\"\n"
        "\"$2\" &\n"
        "rm -- \"$0\"\n",
        encoding="utf-8",
    )
    helper.chmod(0o700)
    subprocess.Popen([str(helper), str(downloaded), str(current)], start_new_session=True)
