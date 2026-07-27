"""Shared helpers: source detection, slugs, token estimates, output writing."""
import json
import re
from pathlib import Path

from . import config


class ExtractError(Exception):
    """User-facing extraction failure: says what failed and the next step."""


def slugify(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return slug[:60].rstrip("-") or "untitled"


def detect_source(source: str) -> str:
    for pattern in config.YOUTUBE_URL_PATTERNS:
        if re.match(pattern, source):
            return "youtube"
    if re.match(config.ARXIV_URL_PATTERN, source):
        return "paper"
    if source.lower().endswith(".pdf"):
        return "paper"
    raise ExtractError(
        f"Unsupported source: {source}\n"
        "Supported: YouTube URLs, arXiv URLs, local .pdf files."
    )


def estimate_tokens(words: int) -> int:
    return int(words * config.TOKENS_PER_WORD)


def write_outputs(work_dir: Path, full_text: str, metadata: dict) -> None:
    work_dir.mkdir(parents=True, exist_ok=True)
    (work_dir / "full_text.txt").write_text(full_text, encoding="utf-8")
    (work_dir / "metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8"
    )
