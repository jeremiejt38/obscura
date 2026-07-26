import re
from dataclasses import dataclass
from typing import List, Tuple, Dict, Any
from PIL import Image, ImageDraw, ImageFilter
import pytesseract


@dataclass
class Box:
    x: int
    y: int
    w: int
    h: int

    @property
    def right(self) -> int:
        return self.x + self.w

    @property
    def bottom(self) -> int:
        return self.y + self.h

    def to_tuple(self) -> Tuple[int, int, int, int]:
        return (self.x, self.y, self.right, self.bottom)

    def union(self, other: "Box") -> "Box":
        x = min(self.x, other.x)
        y = min(self.y, other.y)
        return Box(
            x=x,
            y=y,
            w=max(self.right, other.right) - x,
            h=max(self.bottom, other.bottom) - y,
        )


# Patterns for sensitive data. Each tuple: (compiled regex, label).
SENSITIVE_PATTERNS: List[Tuple[re.Pattern, str]] = [
    # Email addresses
    (re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"), "email"),
    # IPv4 addresses (strict), with optional CIDR
    (
        re.compile(
            r"\b(?:(?:25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}"
            r"(?:25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])"
            r"(?:/\d{1,2})?\b"
        ),
        "ipv4",
    ),
    # Base64 key-like strings (WireGuard, generic secrets)
    (
        re.compile(r"\b[A-Za-z0-9+/]{30,}={0,2}\b"),
        "base64_key",
    ),
    # Hostname:port endpoints (VPN, internal services)
    (
        re.compile(r"\b[a-zA-Z0-9][a-zA-Z0-9.-]*\.[a-zA-Z]{2,}:\d{2,5}\b"),
        "endpoint",
    ),
    # Phone numbers (French + generic international)
    (
        re.compile(
            r"\b(?:\+\d{1,3}|00\d{1,3})[ .-]?\d{1,4}(?:[ .-]?\d{2,4}){1,3}\b|"
            r"\b0[1-9](?:[ .-]?\d{2}){4}\b"
        ),
        "phone",
    ),
    # IBAN
    (
        re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{4}\d{7}(?:[A-Z0-9]?){0,16}\b"),
        "iban",
    ),
    # MAC addresses
    (
        re.compile(r"\b(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}\b"),
        "mac",
    ),
    # French Social Security number (INSEE)
    (
        re.compile(r"\b\d{2}[ .]\d{2}[ .]\d{2}[ .]\d{3}[ .]\d{3}[ .]\d{2}\b|\b\d{15}\b"),
        "ssn_fr",
    ),
    # JWT tokens
    (
        re.compile(r"\beyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*\b"),
        "jwt",
    ),
    # Generic tokens with common prefixes
    (re.compile(r"\b(?:sk|pk|tk|ak)-[a-zA-Z0-9]{10,}\b"), "api_key"),
    # GitHub personal access token
    (re.compile(r"\bghp_[a-zA-Z0-9]{36}\b"), "github_token"),
    # AWS access key ID
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "aws_key"),
    # Credit cards (13-16 digits, with optional spaces/dashes)
    (
        re.compile(r"\b(?:\d[ -]*?){13,16}\b"),
        "credit_card",
    ),
    # Password / secret / token assignments
    (
        re.compile(
            r"(?:password|passwd|pwd|secret|token|api[_-]?key|access[_-]?token)\s*[:=]\s*\S+",
            re.IGNORECASE,
        ),
        "credential",
    ),
    # Private key headers
    (
        re.compile(r"-----BEGIN (?:RSA |OPENSSH |DSA |EC |PGP )?PRIVATE KEY-----"),
        "private_key",
    ),
]


def extract_words(image: Image.Image) -> List[Dict[str, Any]]:
    data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
    words: List[Dict[str, Any]] = []
    for i in range(len(data["text"])):
        text = data["text"][i].strip()
        if not text:
            continue
        conf = int(data["conf"][i])
        if conf < 10:
            continue
        words.append(
            {
                "text": text,
                "box": Box(
                    x=int(data["left"][i]),
                    y=int(data["top"][i]),
                    w=int(data["width"][i]),
                    h=int(data["height"][i]),
                ),
                "line": (
                    data["page_num"][i],
                    data["block_num"][i],
                    data["par_num"][i],
                    data["line_num"][i],
                ),
                "left": int(data["left"][i]),
            }
        )
    return words


def group_words_by_line(words: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
    lines_map: Dict[Tuple[int, int, int, int], List[Dict[str, Any]]] = {}
    for word in words:
        lines_map.setdefault(word["line"], []).append(word)

    sorted_keys = sorted(
        lines_map.keys(), key=lambda k: (lines_map[k][0]["box"].y, lines_map[k][0]["box"].x)
    )
    return [sorted(lines_map[k], key=lambda w: w["left"]) for k in sorted_keys]


def find_sensitive_boxes(line_words: List[Dict[str, Any]]) -> List[Box]:
    regions: List[Box] = []
    n = len(line_words)
    if n == 0:
        return regions

    # Try line-level regex first (most accurate for natural text).
    joined = " ".join(w["text"] for w in line_words)
    char_to_word: List[int] = []
    for idx, w in enumerate(line_words):
        char_to_word.extend([idx] * (len(w["text"]) + 1))  # +1 for the added space
    if char_to_word:
        char_to_word.pop()  # remove trailing space mapping

    matched_patterns = set()
    for pattern, _label in SENSITIVE_PATTERNS:
        for match in pattern.finditer(joined):
            matched_patterns.add(pattern)
            start_char, end_char = match.span()
            # end_char is exclusive; clamp to valid indices.
            start_char = min(start_char, len(char_to_word) - 1)
            end_char = min(end_char - 1, len(char_to_word) - 1)
            start_word_idx = char_to_word[start_char]
            end_word_idx = char_to_word[end_char]
            box = line_words[start_word_idx]["box"]
            for idx in range(start_word_idx + 1, end_word_idx + 1):
                box = box.union(line_words[idx]["box"])
            regions.append(box)

    # Fallback: sliding window with spaces removed, useful for tokens split by OCR.
    for window_size in range(1, min(8, n + 1)):
        for start in range(n - window_size + 1):
            candidate_words = line_words[start : start + window_size]
            compact = "".join(w["text"] for w in candidate_words)
            for pattern, _label in SENSITIVE_PATTERNS:
                if pattern not in matched_patterns and pattern.search(compact):
                    box = candidate_words[0]["box"]
                    for w in candidate_words[1:]:
                        box = box.union(w["box"])
                    regions.append(box)

    return regions


def merge_overlapping_boxes(boxes: List[Box], margin: int = 4) -> List[Box]:
    if not boxes:
        return []

    expanded = [
        Box(b.x - margin, b.y - margin, b.w + 2 * margin, b.h + 2 * margin)
        for b in boxes
    ]
    expanded.sort(key=lambda b: (b.y, b.x))

    merged: List[Box] = [expanded[0]]
    for box in expanded[1:]:
        last = merged[-1]
        if box.x <= last.right and box.y <= last.bottom and last.y <= box.bottom:
            merged[-1] = last.union(box)
        else:
            merged.append(box)

    # Contract by margin to get original-ish size.
    return [
        Box(b.x + margin, b.y + margin, max(1, b.w - 2 * margin), max(1, b.h - 2 * margin))
        for b in merged
    ]


def redact_image(image: Image.Image, mode: str = "black") -> Tuple[Image.Image, int]:
    words = extract_words(image)
    lines = group_words_by_line(words)
    regions: List[Box] = []
    for line in lines:
        regions.extend(find_sensitive_boxes(line))

    if not regions:
        return image, 0

    regions = merge_overlapping_boxes(regions)
    if mode == "blur":
        for box in regions:
            crop = image.crop(box.to_tuple())
            blurred = crop.filter(ImageFilter.GaussianBlur(radius=15))
            image.paste(blurred, box.to_tuple())
    else:
        draw = ImageDraw.Draw(image)
        for box in regions:
            draw.rectangle(box.to_tuple(), fill="black")

    return image, len(regions)
