"""YouTube parser: subtitles via yt-dlp, segmented by video chapters."""
import html
import re
import urllib.request

from .. import config, dependencies, utils
from ..utils import ExtractError

TIMESTAMP_RE = re.compile(r"(?:(\d+):)?(\d{2}):(\d{2})[.,](\d{3})\s*-->")
INLINE_TAG_RE = re.compile(r"<[^>]+>")
HEADER_PREFIXES = ("WEBVTT", "Kind:", "Language:")


def parse_vtt(vtt_text: str) -> list[dict]:
    """Return cues as [{'start_s': float, 'text': str}].

    Auto-captions repeat lines across cues; consecutive duplicates are dropped.
    NOTE comment blocks and cue identifier lines are skipped.
    """
    cues = []
    current_start = None
    in_note = False
    for raw_line in vtt_text.splitlines():
        line = raw_line.strip()
        if not line:
            # A blank line ends the current cue or NOTE block; anything
            # before the next timestamp line is a cue identifier, not text.
            current_start = None
            in_note = False
            continue
        if in_note:
            continue
        if line.startswith("NOTE"):
            in_note = True
            continue
        match = TIMESTAMP_RE.match(line)
        if match:
            hours, minutes, seconds, millis = match.groups()
            current_start = (
                int(hours or 0) * 3600
                + int(minutes) * 60
                + int(seconds)
                + int(millis) / 1000
            )
            continue
        if line.startswith(HEADER_PREFIXES) or current_start is None:
            continue
        text = html.unescape(INLINE_TAG_RE.sub("", line)).strip()
        if not text:
            continue
        if cues and cues[-1]["text"] == text:
            continue
        cues.append({"start_s": current_start, "text": text})
    return cues


def build_segments(chapters, duration_s) -> list[dict]:
    """Segment boundaries from video chapters, else fixed windows."""
    if chapters:
        return [
            {"title": ch["title"], "start_s": int(ch["start_time"])}
            for ch in chapters
        ]
    if not duration_s:
        return [{"title": "Full transcript", "start_s": 0}]
    window = config.DEFAULT_SEGMENT_WINDOW_S
    return [
        {"title": f"Part {i + 1}", "start_s": start}
        for i, start in enumerate(range(0, int(duration_s), window))
    ]


def segment_text(cues, segments):
    """Assign cues to segments; return (full_text, segments with offsets)."""
    # The first segment absorbs everything from t=0 even if its chapter
    # starts later, so no cue is ever dropped.
    starts = [0] + [seg["start_s"] for seg in segments[1:]]
    chunks = []
    out_segments = []
    offset = 0
    for i, seg in enumerate(segments):
        end = starts[i + 1] if i + 1 < len(starts) else float("inf")
        texts = [c["text"] for c in cues if starts[i] <= c["start_s"] < end]
        chunk = (
            f"=== {seg['title']} [t={seg['start_s']}s] ===\n"
            + "\n".join(texts)
            + "\n\n"
        )
        out_segments.append(
            {
                "title": seg["title"],
                "start_s": seg["start_s"],
                "pages": None,
                "offset": offset,
            }
        )
        chunks.append(chunk)
        offset += len(chunk)
    return "".join(chunks), out_segments


def _fetch(url: str) -> str:
    with urllib.request.urlopen(
        url, timeout=config.FETCH_TIMEOUT_S
    ) as response:
        return response.read().decode("utf-8")


def _pick_track(info: dict):
    """Prefer manual subtitles over auto captions; prefer English.

    Only languages that offer a vtt format count; English variants
    (en, en-US, en-GB, ...) are all recognized as English.
    """
    for kind in ("subtitles", "automatic_captions"):
        tracks = info.get(kind) or {}
        with_vtt = {
            lang: fmts
            for lang, fmts in tracks.items()
            if any(fmt.get("ext") == "vtt" for fmt in fmts)
        }
        if not with_vtt:
            continue
        english = sorted(
            lang for lang in with_vtt
            if lang == "en" or lang.startswith("en-")
        )
        lang = english[0] if english else sorted(with_vtt)[0]
        for fmt in with_vtt[lang]:
            if fmt.get("ext") == "vtt":
                return kind, lang, fmt["url"]
    return None, None, None


def parse(url: str):
    ydl_mod = dependencies.require("yt_dlp")
    opts = {"quiet": True, "skip_download": True, "noplaylist": True}
    with ydl_mod.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)

    kind, lang, vtt_url = _pick_track(info)
    if not vtt_url:
        raise ExtractError(
            f"No captions available for {url}.\n"
            "v1 needs manual or auto captions; Whisper transcription "
            "is not supported yet."
        )
    cues = parse_vtt(_fetch(vtt_url))
    if not cues:
        raise ExtractError(
            f"Caption download for {url} returned no cues ({lang}).\n"
            "YouTube sometimes serves empty caption files - retry, or try "
            "another caption language or video."
        )
    segments = build_segments(info.get("chapters"), info.get("duration"))
    full_text, out_segments = segment_text(cues, segments)
    words = len(full_text.split())
    metadata = {
        "source_type": "youtube",
        "title": info.get("title") or "Untitled video",
        "origin": info.get("webpage_url") or url,
        "channel": info.get("channel"),
        "upload_date": info.get("upload_date"),
        "duration_s": info.get("duration"),
        "language": lang,
        "captions": "manual" if kind == "subtitles" else "auto",
        "words": words,
        "est_tokens": utils.estimate_tokens(words),
        "segments": out_segments,
    }
    return full_text, metadata
