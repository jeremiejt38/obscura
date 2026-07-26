import hashlib
import io
import os
import platform
import shutil
import subprocess
from typing import Optional, Tuple

from PIL import Image


def _is_wayland() -> bool:
    return bool(os.environ.get("WAYLAND_DISPLAY"))


def _linux_read_cmd() -> list:
    if _is_wayland() and shutil.which("wl-paste"):
        return ["wl-paste", "--type", "image/png"]
    if shutil.which("xclip"):
        return ["xclip", "-selection", "clipboard", "-t", "image/png", "-o"]
    raise RuntimeError("No Linux image clipboard tool found. Install xclip or wl-clipboard.")


def _linux_write_cmd() -> list:
    if _is_wayland() and shutil.which("wl-copy"):
        return ["wl-copy", "--type", "image/png"]
    if shutil.which("xclip"):
        return ["xclip", "-selection", "clipboard", "-t", "image/png"]
    raise RuntimeError("No Linux image clipboard tool found. Install xclip or wl-clipboard.")


def _image_from_bytes(data: bytes) -> Optional[Image.Image]:
    try:
        with Image.open(io.BytesIO(data)) as image:
            return image.convert("RGB")
    except OSError:
        return None


def _read_windows_image() -> Optional[Image.Image]:
    import win32clipboard
    import win32con

    try:
        win32clipboard.OpenClipboard()
        if not win32clipboard.IsClipboardFormatAvailable(win32con.CF_DIB):
            return None
        dib = win32clipboard.GetClipboardData(win32con.CF_DIB)
    finally:
        try:
            win32clipboard.CloseClipboard()
        except win32clipboard.error:
            pass
    return _image_from_bytes(b"BM" + (len(dib) + 14).to_bytes(4, "little") + b"\x00\x00\x00\x00\x36\x00\x00\x00" + dib)


def _write_windows_image(image: Image.Image) -> None:
    import win32clipboard
    import win32con

    output = io.BytesIO()
    image.convert("RGB").save(output, format="BMP")
    win32clipboard.OpenClipboard()
    try:
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32con.CF_DIB, output.getvalue()[14:])
    finally:
        win32clipboard.CloseClipboard()


def _read_macos_image() -> Optional[Image.Image]:
    from AppKit import NSPasteboard, NSPasteboardTypePNG

    data = NSPasteboard.generalPasteboard().dataForType_(NSPasteboardTypePNG)
    return _image_from_bytes(bytes(data)) if data is not None else None


def _write_macos_image(data: bytes) -> None:
    from AppKit import NSData, NSPasteboard, NSPasteboardTypePNG

    pasteboard = NSPasteboard.generalPasteboard()
    pasteboard.clearContents()
    pasteboard.setData_forType_(NSData.dataWithBytes_length_(data, len(data)), NSPasteboardTypePNG)


def read_image_from_clipboard() -> Tuple[Optional[Image.Image], Optional[str]]:
    system = platform.system()
    if system == "Linux":
        try:
            raw = subprocess.check_output(_linux_read_cmd(), stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError:
            return None, None
        image = _image_from_bytes(raw)
        return image, hashlib.sha256(raw).hexdigest()[:16] if raw else None
    if system == "Windows":
        image = _read_windows_image()
    elif system == "Darwin":
        image = _read_macos_image()
    else:
        raise RuntimeError(f"Unsupported platform: {system}")
    if image is None:
        return None, None
    output = io.BytesIO()
    image.save(output, format="PNG")
    return image, hashlib.sha256(output.getvalue()).hexdigest()[:16]


def write_image_to_clipboard(image: Image.Image) -> str:
    output = io.BytesIO()
    image.convert("RGB").save(output, format="PNG")
    data = output.getvalue()
    system = platform.system()
    if system == "Linux":
        proc = subprocess.Popen(_linux_write_cmd(), stdin=subprocess.PIPE)
        proc.communicate(data)
        if proc.returncode != 0:
            raise RuntimeError("Linux clipboard tool failed to write image")
    elif system == "Windows":
        _write_windows_image(image)
    elif system == "Darwin":
        _write_macos_image(data)
    else:
        raise RuntimeError(f"Unsupported platform: {system}")
    return hashlib.sha256(data).hexdigest()[:16]


def has_clipboard_tool() -> bool:
    system = platform.system()
    if system == "Linux":
        try:
            _linux_read_cmd()
            return True
        except RuntimeError:
            return False
    if system == "Windows":
        try:
            import win32clipboard
        except ImportError:
            return False
        return True
    if system == "Darwin":
        try:
            import AppKit
        except ImportError:
            return False
        return True
    return False
