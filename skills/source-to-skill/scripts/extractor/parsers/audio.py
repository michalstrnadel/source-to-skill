"""Audio parser: podcasts, media URLs and local files via local Whisper.

Remote sources are downloaded with yt-dlp (Apple Podcasts, direct .mp3
links, and any of yt-dlp's supported sites when forced with --type audio);
local audio/video files are transcribed in place. Segments follow the
episode's chapters when it has them, else fixed windows - the same
contract as YouTube videos, so every segment keeps its start second.
"""
import re
from pathlib import Path

from .. import dependencies, media, transcribe, utils
from ..utils import ExtractError
from .youtube import build_segments, segment_text


def deep_link_template(origin: str):
    """URL template with a {s} placeholder for seconds, or None.

    YouTube takes &t=/ ?t=, Vimeo #t=Ns, direct media files the W3C
    media fragment #t=N. Podcast pages and local files have no
    seekable link; skills cite [mm:ss] timestamps instead.
    """
    if not re.match(r"https?://", origin):
        return None
    base = origin.split("#", 1)[0]
    if re.match(r"https?://(?:[\w-]+\.)?(?:youtube\.com|youtu\.be)/", base):
        return base + ("&" if "?" in base else "?") + "t={s}s"
    if re.match(r"https?://(?:www\.|player\.)?vimeo\.com/", base):
        return base + "#t={s}s"
    if utils._is_media_path(base):
        return base + "#t={s}"
    return None


def _local(source: str):
    path = Path(source).expanduser()
    if not path.is_file():
        raise ExtractError(
            f"Audio file not found: {source}\nCheck the path and retry."
        )
    title = re.sub(r"[_-]+", " ", path.stem).strip() or "Untitled recording"
    info = {"title": title, "webpage_url": str(path.resolve())}
    return info, path, False


def _remote(source: str):
    ydl_mod = dependencies.require("yt_dlp")
    info, path = media.download_audio(ydl_mod, source)
    return info, path, True


def parse(source: str):
    is_url = re.match(r"https?://", source) is not None
    info, path, downloaded = (_remote if is_url else _local)(source)
    try:
        cues, language, label = transcribe.transcribe(path)
    finally:
        if downloaded:
            path.unlink(missing_ok=True)
    duration = info.get("duration") or int(cues[-1]["start_s"]) + 1
    segments = build_segments(info.get("chapters"), duration)
    full_text, out_segments = segment_text(cues, segments)
    words = len(full_text.split())
    origin = info.get("webpage_url") or source
    metadata = {
        "source_type": "audio",
        "title": info.get("title") or "Untitled audio",
        "origin": origin,
        "channel": (
            info.get("series") or info.get("channel") or info.get("uploader")
        ),
        "upload_date": info.get("upload_date"),
        "duration_s": duration,
        "language": language,
        "captions": "whisper",
        "transcribed_with": label,
        "deep_link_template": deep_link_template(origin),
        "words": words,
        "est_tokens": utils.estimate_tokens(words),
        "segments": out_segments,
    }
    return full_text, metadata
