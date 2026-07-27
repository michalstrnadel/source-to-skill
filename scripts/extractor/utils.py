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


def _possible_types(source: str) -> tuple:
    """Source types this source can plausibly be, best guess first.

    Detection order: youtube -> playlist -> arxiv -> github repo ->
    generic http(s) article -> .pdf -> .epub. Any http(s) URL can also
    be forced to article; a watch URL with a list= param can be forced
    to playlist (and is playlist-only when it has no v= param).
    """
    as_article = ("article",) if re.match(r"https?://", source) else ()
    for pattern in config.YOUTUBE_URL_PATTERNS:
        if not re.match(pattern, source):
            continue
        has_list = re.search(r"[?&]list=", source) is not None
        is_watch = re.match(config.YOUTUBE_URL_PATTERNS[0], source) is not None
        if has_list and is_watch and not re.search(r"[?&]v=", source):
            # A watch URL with list= but no v= identifies only the
            # playlist; there is no video for the single-video parser.
            return ("playlist",) + as_article
        as_playlist = ("playlist",) if has_list else ()
        return ("youtube",) + as_playlist + as_article
    if re.match(config.PLAYLIST_URL_PATTERN, source):
        return ("playlist",) + as_article
    if re.match(config.ARXIV_URL_PATTERN, source):
        return ("paper",) + as_article
    if re.match(config.GITHUB_REPO_PATTERN, source):
        return ("repo",) + as_article
    if as_article:
        return as_article
    lowered = source.lower()
    if lowered.endswith(".pdf"):
        return ("paper", "book")
    if lowered.endswith(".epub"):
        return ("book",)
    return ()


def detect_source(source: str, forced=None) -> str:
    """Detect the source type; `forced` overrides it after validation."""
    if forced is not None and forced not in config.SOURCE_TYPES:
        raise ExtractError(
            f"Unknown source type: {forced}\n"
            f"Supported types: {', '.join(config.SOURCE_TYPES)}."
        )
    possible = _possible_types(source)
    if not possible:
        raise ExtractError(
            f"Unsupported source: {source}\n"
            "Supported: YouTube video and playlist URLs, arXiv URLs, "
            "GitHub repo URLs, web article URLs (http/https), "
            "local .pdf and .epub files."
        )
    if forced is None:
        return possible[0]
    if forced not in possible:
        raise ExtractError(
            f"{source} cannot be extracted as {forced} "
            f"(this source can be: {', '.join(possible)}).\n"
            f"Drop --type or use --type {possible[0]}."
        )
    return forced


def estimate_tokens(words: int) -> int:
    return int(words * config.TOKENS_PER_WORD)


def write_outputs(work_dir: Path, full_text: str, metadata: dict) -> None:
    work_dir.mkdir(parents=True, exist_ok=True)
    (work_dir / "full_text.txt").write_text(full_text, encoding="utf-8")
    (work_dir / "metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8"
    )
