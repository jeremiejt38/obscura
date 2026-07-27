from dataclasses import dataclass
from typing import Iterable

from PIL import Image, ImageDraw, ImageFilter

from .config import AppConfig, CustomRule
from .redactor import Box, SENSITIVE_PATTERNS, extract_words, find_sensitive_boxes, group_words_by_line, merge_overlapping_boxes


@dataclass(frozen=True)
class Detection:
    category: str
    box: Box


@dataclass
class RedactionResult:
    image: Image.Image
    detections: list[Detection]

    @property
    def count(self) -> int:
        return len(self.detections)


def _patterns(config: AppConfig) -> list[tuple[object, str]]:
    patterns = [(pattern, category) for pattern, category in SENSITIVE_PATTERNS if category in config.active_categories]
    for rule in config.custom_rules:
        if not rule.enabled or not rule.value:
            continue
        import re

        expression = rule.value if rule.is_regex else re.escape(rule.value)
        try:
            patterns.append((re.compile(expression, re.IGNORECASE), f"custom:{rule.name}"))
        except re.error:
            continue
    return patterns


def find_detections(image: Image.Image, config: AppConfig) -> list[Detection]:
    words = extract_words(image, languages="+".join(config.ocr_languages), confidence=config.ocr_confidence)
    patterns = _patterns(config)
    detections: list[Detection] = []
    for line in group_words_by_line(words):
        for box, category in find_sensitive_boxes(line, patterns=patterns, include_categories=True):
            detections.append(Detection(category=category, box=box))
    merged = merge_overlapping_boxes([item.box for item in detections])
    return [Detection(category="sensitive", box=box) for box in merged]


def _pixelate(image: Image.Image, box: Box, pixel_size: int) -> None:
    crop = image.crop(box.to_tuple())
    width, height = crop.size
    reduced = crop.resize((max(1, width // pixel_size), max(1, height // pixel_size)), Image.Resampling.NEAREST)
    image.paste(reduced.resize((width, height), Image.Resampling.NEAREST), box.to_tuple())


def apply_redactions(image: Image.Image, detections: Iterable[Detection], config: AppConfig) -> Image.Image:
    output = image.copy()
    for detection in detections:
        box = detection.box
        if config.redaction_mode == "blur":
            crop = output.crop(box.to_tuple())
            output.paste(crop.filter(ImageFilter.GaussianBlur(radius=config.blur_radius)), box.to_tuple())
        elif config.redaction_mode == "pixelate":
            _pixelate(output, box, config.pixel_size)
        else:
            ImageDraw.Draw(output).rectangle(box.to_tuple(), fill="black")
    return output


def redact(image: Image.Image, config: AppConfig) -> RedactionResult:
    detections = find_detections(image, config)
    return RedactionResult(image=apply_redactions(image, detections, config), detections=detections)
