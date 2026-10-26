"""Shared helpers: source detection, slugs, token estimates, output writing."""
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from . import __version__, config


class ExtractError(Exception):
    """User-facing extraction failure: says what failed and the next step."""


class _PermanentRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Follow 308 like 307 (urllib learned 308 only in Python 3.11)."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return super().redirect_request(
            req, fp, 307 if code == 308 else code, msg, headers, newurl
        )

    http_error_308 = urllib.request.HTTPRedirectHandler.http_error_302


def follow_permanent_redirects() -> None:
    """Make urlopen() follow HTTP 308 on Python 3.10, as 3.11+ does."""
    if sys.version_info < (3, 11):
        urllib.request.install_opener(
            urllib.request.build_opener(_PermanentRedirectHandler)
        )


def slugify(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return slug[:60].rstrip("-") or "untitled"


def _is_media_path(source: str) -> bool:
    """True when a URL path or file name ends in an audio/video extension."""
    path = re.split(r"[?#]", source, maxsplit=1)[0].lower()
    return path.endswith(config.MEDIA_EXTENSIONS)


def _possible_types(source: str) -> tuple:
    """Source types this source can plausibly be, best guess first.

    Detection order: youtube video -> channel -> playlist -> llms.txt /
    llms-full.txt docs -> podcast RSS feed (a playlist of episodes) ->
    podcast page or direct media URL -> arxiv -> github repo -> generic
    http(s) article -> local directory (notes) -> .pdf -> .epub -> local
    audio/video file. Any http(s) URL can also be forced to article or
    audio (yt-dlp downloads from 1000+ sites); a generic web URL can be
    forced to docs (its llms.txt is looked up); a watch URL with a list=
    param can be forced to playlist (and is playlist-only when it has no
    v= param).
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
    if is_http and re.match(config.LLMS_TXT_URL_PATTERN, source):
        return with_others("docs")
    if is_http and re.match(config.FEED_URL_PATTERN, source):
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
        return as_other + ("docs",)
    if Path(source).expanduser().is_dir():
        return ("notes",)
    lowered = source.lower()
    if lowered.endswith(".pdf"):
        return ("paper", "book")
    if lowered.endswith(".epub"):
        return ("book",)
    if _is_media_path(source):
        return ("audio",)
    return ()


def is_feed_url(source: str) -> bool:
    return re.match(config.FEED_URL_PATTERN, source) is not None


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
            "and audio/video URLs, arXiv URLs, GitHub repo URLs, docs "
            "sites (llms.txt / llms-full.txt URLs), web article URLs "
            "(http/https), local .pdf, .epub and audio/video files, local "
            "notes folders (Obsidian vaults, Markdown folders)."
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
    """Stable identity of a segment across re-extractions.

    Its URL when it has one, else an explicit `key` (notes: the relative
    file path), else its title. Repo segments carry `path` too but stay
    keyed by title so refresh manifests written earlier keep matching.
    """
    return segment.get("url") or segment.get("key") or segment["title"]


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
