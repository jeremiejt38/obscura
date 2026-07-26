# Obscura

Obscura is an offline, cross-platform screenshot privacy tool. It runs Tesseract OCR locally, detects common sensitive values with regular expressions, redacts matching regions, and can replace an image directly in the clipboard.

No image content is sent to a network service.

## Features

- Local OCR powered by Tesseract.
- Detection for emails, IP addresses, JWTs, API keys, IBANs, phone numbers, card numbers, password assignments, and private-key headers.
- Black-box and Gaussian-blur redaction modes.
- Single-file processing, clipboard monitoring, and screenshot-folder monitoring.
- Linux, Windows, and macOS clipboard backends.

## Requirements

- Python 3.9 or newer.
- Tesseract OCR installed on the operating system.
- An image clipboard backend for the platform.

### Linux

Install Tesseract and one clipboard backend:

```bash
sudo apt update
sudo apt install tesseract-ocr xclip
```

For Wayland, install `wl-clipboard` instead of or alongside `xclip`:

```bash
sudo apt install tesseract-ocr wl-clipboard
```

### macOS

```bash
brew install tesseract
```

The Python installation installs the native Cocoa clipboard binding automatically.

### Windows

Install Tesseract with its installer and ensure its installation directory is on `PATH`. The Python installation installs the Windows clipboard binding automatically.

## Installation

Install directly from a local checkout:

```bash
python -m venv .venv
```

Linux and macOS:

```bash
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install .
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install .
```

The `obscura` command is then available in the active environment.

## Usage

### Process one image

```bash
obscura /path/to/screenshot.png
```

The output is written next to the source as `screenshot_redacted.png`.

### Copy a processed image to the clipboard

```bash
obscura /path/to/screenshot.png --copy
```

### Use Gaussian blur

```bash
obscura /path/to/screenshot.png --blur
```

### Watch the image clipboard

```bash
obscura
```

Every new clipboard image is scanned and replaced only when a sensitive region is found. Stop the watcher with `Ctrl+C`.

### Watch a screenshot folder

```bash
obscura ~/Pictures/Screenshots --watch-dir --copy
```

Generated files whose stem ends in `_redacted` are ignored, preventing the watcher from reprocessing its own output. Change that suffix with `--suffix`.

## Detection and privacy

Patterns live in `obscura.redactor.SENSITIVE_PATTERNS`. OCR can make mistakes, so review redacted output before sharing it. The original source file is never overwritten; clipboard mode replaces only the current clipboard image.

## Development

```bash
python -m pip install . pytest
python -m pytest
```

GitHub Actions runs tests on Linux, Windows, and macOS. Pushing a three-part version tag such as `v0.1.0` builds one PyInstaller executable per platform and creates a GitHub Release.

Use `feature/*` branches and Conventional Commits. Default to patch releases; increment the minor version only for a meaningful milestone. Version `1.0.0` requires explicit approval.

## License

[MIT](LICENSE)
