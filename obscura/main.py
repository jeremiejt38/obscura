#!/usr/bin/env python3
import argparse
import os
import sys
import time
from pathlib import Path

from PIL import Image

from .clipboard import has_clipboard_tool, read_image_from_clipboard, write_image_to_clipboard
from .redactor import redact_image
from .watcher import watch_directory


def process_image(image: Image.Image, mode: str = "black") -> tuple:
    redacted, count = redact_image(image, mode=mode)
    return redacted, count


def process_file(path: str, copy_to_clipboard: bool = False, suffix: str = "_redacted", mode: str = "black") -> str:
    image = Image.open(path).convert("RGB")
    redacted, count = process_image(image, mode=mode)
    input_path = Path(path)
    output_path = input_path.parent / f"{input_path.stem}{suffix}{input_path.suffix}"
    redacted.save(output_path)
    print(f"[✓] Redacted {count} sensitive region(s) -> {output_path}")

    if copy_to_clipboard:
        write_image_to_clipboard(redacted)
        print("[✓] Redacted image copied to clipboard")

    return output_path


def clipboard_mode(poll_interval: float = 0.5, mode: str = "black") -> None:
    if not has_clipboard_tool():
        print(
            "[ERROR] No clipboard tool found. Install xclip (X11) or wl-clipboard (Wayland).",
            file=sys.stderr,
        )
        sys.exit(1)

    print("[INFO] Watching clipboard for images. Press Ctrl+C to stop.")
    last_processed_digest: str = ""

    while True:
        try:
            image, digest = read_image_from_clipboard()
            if image is None or digest == last_processed_digest:
                time.sleep(poll_interval)
                continue

            redacted, count = process_image(image, mode=mode)
            if count == 0:
                print(f"[INFO] Clipboard image scanned, nothing sensitive found.")
                last_processed_digest = digest
                time.sleep(poll_interval)
                continue

            new_digest = write_image_to_clipboard(redacted)
            print(f"[✓] Redacted {count} sensitive region(s) and updated clipboard.")
            last_processed_digest = new_digest
        except Exception as exc:
            print(f"[ERROR] {exc}", file=sys.stderr)
        time.sleep(poll_interval)


def directory_mode(
    directory: str,
    copy_to_clipboard: bool = False,
    suffix: str = "_redacted",
    mode: str = "black",
) -> None:
    if not os.path.isdir(directory):
        print(f"[ERROR] Directory does not exist: {directory}", file=sys.stderr)
        sys.exit(1)

    print(f"[INFO] Watching {directory} for new screenshots. Press Ctrl+C to stop.")

    def handle(path: str):
        try:
            print(f"[INFO] New screenshot detected: {path}")
            process_file(path, copy_to_clipboard=copy_to_clipboard, suffix=suffix, mode=mode)
        except Exception as exc:
            print(f"[ERROR] Failed to process {path}: {exc}", file=sys.stderr)

    watch_directory(directory, handle, ignored_stem_suffix=suffix)


def main():
    parser = argparse.ArgumentParser(
        description="Auto-redact sensitive text from screenshots using local OCR."
    )
    parser.add_argument(
        "path",
        nargs="?",
        help="Image file or directory to process. If omitted, watches the clipboard.",
    )
    parser.add_argument(
        "--watch-dir",
        action="store_true",
        help="Treat PATH as a directory to watch for new screenshots.",
    )
    parser.add_argument(
        "--copy",
        action="store_true",
        help="Copy the redacted result back to the clipboard.",
    )
    parser.add_argument(
        "--suffix",
        default="_redacted",
        help="Suffix for redacted files (default: _redacted).",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=0.5,
        help="Clipboard polling interval in seconds (default: 0.5).",
    )
    parser.add_argument(
        "--blur",
        dest="mode",
        action="store_const",
        const="blur",
        default="black",
        help="Use Gaussian blur instead of a black rectangle for redaction.",
    )
    args = parser.parse_args()

    if args.path and not args.watch_dir:
        if not os.path.isfile(args.path):
            print(f"[ERROR] File not found: {args.path}", file=sys.stderr)
            sys.exit(1)
        process_file(args.path, copy_to_clipboard=args.copy, suffix=args.suffix, mode=args.mode)
    elif args.path and args.watch_dir:
        directory_mode(args.path, copy_to_clipboard=args.copy, suffix=args.suffix, mode=args.mode)
    else:
        clipboard_mode(poll_interval=args.interval, mode=args.mode)


if __name__ == "__main__":
    main()
