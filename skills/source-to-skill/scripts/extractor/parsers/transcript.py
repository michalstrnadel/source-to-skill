"""Transcript parser: local .srt/.vtt subtitle and meeting-transcript files.

Zoom, Teams and Google Meet export WebVTT (Teams marks speakers with
`<v Name>` voice tags, Zoom with `Name:` prefixes); downloaded captions
are usually SubRip. Cues are read with the YouTube VTT parser (its
timestamp pattern accepts SRT's comma too) and segmented into the same
fixed windows with inline [t=Ns] markers, so the output matches the
audio/video contract.
"""
import re
from pathlib import Path

from .. import utils
from ..utils import ExtractError
from .youtube import build_segments, parse_vtt, segment_text

# <v Name>, <v.loud Name> -> "Name: "
VOICE_RE = re.compile(r"<v(?:\.[\w.-]+)*\s+([^>]+?)\s*>")
# SubStation overrides some SRT files carry: {\an8}, {\i1}
SSA_RE = re.compile(r"\{\\[^}]*\}")
END_RE = re.compile(r"-->\s*(?:(\d+):)?(\d{2}):(\d{2})[.,](\d{3})")
LANGUAGE_RE = re.compile(r"(?m)^Language:\s*(\S+)")
SPEAKER_RE = re.compile(r"^([^\W\d_][\w'.-]*(?: [^\W\d_][\w'.-]*){0,3}):\s")


def _read(path: Path) -> str:
    raw = path.read_bytes()
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        # Older subtitle files are often Windows-1252 (a Latin-1
        # superset); its few undefined bytes become U+FFFD.
        return raw.decode("cp1252", errors="replace")


def _speakers(cues, voiced) -> list:
    """Speaker names in order of first appearance.

    Voice-tag names always count; a `Name:` prefix counts once it opens
    two or more cues, so a one-off "Note:" or "Update:" is not a speaker.
    """
    counts = {}
    order = []
    for cue in cues:
        match = SPEAKER_RE.match(cue["text"])
        if not match:
            continue
        name = match.group(1)
        if not all(token[0].isupper() for token in name.split()):
            continue
        if name not in counts:
            order.append(name)
        counts[name] = counts.get(name, 0) + 1
    return [n for n in order if n in voiced or counts[n] >= 2]


def parse(source: str):
    if re.match(r"https?://", source):
        raise ExtractError(
            f"Unsupported transcript URL: {source}\n"
            "Transcripts are read from local files - download the "
            ".srt/.vtt file and pass its path."
        )
    path = Path(source).expanduser()
    if not path.is_file():
        raise ExtractError(
            f"Transcript file not found: {source}\nCheck the path and retry."
        )
    text = _read(path)
    voiced = {" ".join(name.split()) for name in VOICE_RE.findall(text)}
    text = SSA_RE.sub("", VOICE_RE.sub(r"\1: ", text))
    # No dedupe: only auto-captions roll lines; a file's repeats are real.
    cues = parse_vtt(text, dedupe=False)
    if not cues:
        raise ExtractError(
            f"{path} has no cues (no timestamped subtitle text found).\n"
            "Check that it is a SubRip (.srt) or WebVTT (.vtt) file."
        )
    ends = [
        int(h or 0) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000
        for h, m, s, ms in END_RE.findall(text)
    ]
    duration = int(max(ends + [cues[-1]["start_s"] + 1]))
    full_text, segments = segment_text(cues, build_segments(None, duration))
    # Only the WebVTT header (before the first cue) declares a language.
    language = LANGUAGE_RE.search(text.split("-->", 1)[0])
    words = len(full_text.split())
    metadata = {
        "source_type": "transcript",
        "format": path.suffix.lower().lstrip("."),
        "title": (
            re.sub(r"[_-]+", " ", path.stem).strip() or "Untitled transcript"
        ),
        "origin": source,
        "duration_s": duration,
        "language": language.group(1) if language else None,
        "captions": "file",
        "speakers": _speakers(cues, voiced),
        "deep_link_template": None,
        "words": words,
        "est_tokens": utils.estimate_tokens(words),
        "segments": segments,
    }
    return full_text, metadata
