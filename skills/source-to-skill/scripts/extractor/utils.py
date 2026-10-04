"""Shared helpers: source detection, slugs, token estimates, output writing."""
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from . import __version__, config


class ExtractError(Exception):
    """User-facing extraction failure: says what failed and the next step."""


def slugify(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return slug[:60].rstrip("-") or "untitled"


def _is_media_path(source: str) -> bool:
    """True when a URL path or file name ends in an audio/video extension."""
    path = re.split(r"[?#]", source, maxsplit=1)[0].lower()
    return path.endswith(config.MEDIA_EXTENSIONS)


def _possible_types(source: str) -> tuple:
    """Source types this source can plausibly be, best guess first.

    Detection order: youtube video -> channel -> playlist -> podcast page
    or direct media URL -> arxiv -> github repo -> generic http(s)
    article -> .pdf -> .epub -> local audio/video file. Any http(s) URL
    can also be forced to article or audio (yt-dlp downloads from 1000+
    sites); a watch URL with a list= param can be forced to playlist
    (and is playlist-only when it has no v= param).
    """
    is_http = re.match(r"https?://", source) is not None
    as_other = ("article", "audio") if is_http else ()

    def with_others(*types):
        return types + tuple(t for t in as_other if t not in types)

    for pattern in config.YOUTUBE_URL_PATTERNS:
        if not re.match(pattern, source):
            continue
        has_list = re.search(r"[?&]list=", source) is not None
        is_watch = re.match(config.YOUTUBE_URL_PATTERNS[0], source) is not None
        if has_list and is_watch and not re.search(r"[?&]v=", source):
            # A watch URL with list= but no v= identifies only the
            # playlist; there is no video for the single-video parser.
            return with_others("playlist")
        as_playlist = ("playlist",) if has_list else ()
        return with_others("youtube", *as_playlist)
    if re.match(config.CHANNEL_URL_PATTERN, source):
        return with_others("playlist")
    if re.match(config.PLAYLIST_URL_PATTERN, source):
        return with_others("playlist")
    if is_http and (
        any(re.match(p, source) for p in config.PODCAST_URL_PATTERNS)
        or _is_media_path(source)
    ):
        return with_others("audio")
    if re.match(config.ARXIV_URL_PATTERN, source):
        return with_others("paper")
    if re.match(config.GITHUB_REPO_PATTERN, source):
        return with_others("repo")
    if is_http:
        return as_other
    lowered = source.lower()
    if lowered.endswith(".pdf"):
        return ("paper", "book")
    if lowered.endswith(".epub"):
        return ("book",)
    if _is_media_path(source):
        return ("audio",)
    return ()


def is_channel_url(source: str) -> bool:
    return re.match(config.CHANNEL_URL_PATTERN, source) is not None


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
            "Supported: YouTube video, playlist and channel URLs, podcast "
            "and audio/video URLs, arXiv URLs, GitHub repo URLs, web "
            "article URLs (http/https), local .pdf, .epub and audio/video "
            "files."
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


def segment_key(segment: dict) -> str:
    """Stable identity of a segment across re-extractions."""
    return segment.get("url") or segment["title"]


def write_manifest(
    work_dir: Path, source: str, metadata: dict, options: dict
) -> None:
    """Write source.json: what was extracted, from where, and how.

    The generated skill keeps a copy so it can be refreshed later
    (re-extract the same origin, then diff with tools/diff_source.py).
    """
    if not re.match(r"https?://", source):
        # Local files: never publish an absolute home path in a skill.
        home = str(Path.home())
        source = str(Path(source).expanduser())
        if source.startswith(home + "/"):
            source = "~" + source[len(home):]
    manifest = {
        "source": source,
        "origin": (
            metadata.get("origin", source)
            if re.match(r"https?://", metadata.get("origin", ""))
            else source
        ),
        "source_type": metadata["source_type"],
        "title": metadata["title"],
        "est_tokens": metadata.get("est_tokens"),
        "extracted_at": datetime.now(timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        ),
        "extractor_version": __version__,
        "options": {
            key: value
            for key, value in options.items()
            if key in ("type", "limit", "transcribe") and value
        },
        "segments": [
            {"key": segment_key(seg), "title": seg["title"]}
            for seg in metadata["segments"]
        ],
    }
    work_dir.mkdir(parents=True, exist_ok=True)
    (work_dir / "source.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )
