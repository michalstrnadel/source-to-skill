"""YouTube playlist parser: yt-dlp flat listing + per-video captions."""
import sys

from .. import config, dependencies, utils
from ..utils import ExtractError
from .youtube import _fetch, _pick_track, parse_vtt


def _video_transcript(ydl_mod, video_url):
    """Return (video info, transcript) or raise ExtractError."""
    opts = {"quiet": True, "skip_download": True, "noplaylist": True}
    with ydl_mod.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(video_url, download=False)
    _, lang, vtt_url = _pick_track(info)
    if not vtt_url:
        raise ExtractError("no captions available")
    cues = parse_vtt(_fetch(vtt_url))
    if not cues:
        raise ExtractError(f"caption download returned no cues ({lang})")
    return info, "\n".join(cue["text"] for cue in cues)


def parse(url: str):
    ydl_mod = dependencies.require("yt_dlp")
    opts = {"quiet": True, "skip_download": True, "extract_flat": True}
    with ydl_mod.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)

    title = info.get("title") or "Untitled playlist"
    entries = [entry for entry in (info.get("entries") or []) if entry]
    if not entries:
        raise ExtractError(
            f"Playlist {url} has no videos.\n"
            "Check the URL; private or empty playlists cannot be extracted."
        )
    if len(entries) > config.PLAYLIST_WARN_VIDEOS:
        print(
            f"WARNING: playlist has {len(entries)} videos "
            f"(over {config.PLAYLIST_WARN_VIDEOS}); extraction may take a "
            "while and skill generation will be costly.",
            file=sys.stderr,
        )

    chunks = []
    segments = []
    skipped = []
    offset = 0
    for number, entry in enumerate(entries, start=1):
        video_title = entry.get("title") or f"Video {number}"
        video_url = entry.get("url")
        if not video_url and entry.get("id"):
            video_url = f"https://www.youtube.com/watch?v={entry['id']}"
        if not video_url:
            reason = "playlist entry has no url or id"
            skipped.append(
                {"title": video_title, "url": None, "reason": reason}
            )
            print(
                f"WARNING: skipping [{number:02d}] {video_title}: {reason}",
                file=sys.stderr,
            )
            continue
        try:
            video_info, transcript = _video_transcript(ydl_mod, video_url)
        except Exception as err:  # one bad video never fails the playlist
            # str(err) can be empty (e.g. bare TimeoutError()); fall back
            # to the type name instead of crashing on [0] of an empty list.
            reason = (
                (str(err).splitlines() or [type(err).__name__])[0]
                or type(err).__name__
            )
            skipped.append(
                {"title": video_title, "url": video_url, "reason": reason}
            )
            print(
                f"WARNING: skipping [{number:02d}] {video_title}: {reason}",
                file=sys.stderr,
            )
            continue
        video_title = video_info.get("title") or video_title
        chunk = (
            f"=== [{number:02d}] {video_title} ===\n"
            f"{video_url}\n{transcript}\n\n"
        )
        segments.append(
            {
                "title": video_title,
                "start_s": None,
                "pages": None,
                "offset": offset,
                "url": video_url,
            }
        )
        chunks.append(chunk)
        offset += len(chunk)

    if not chunks:
        raise ExtractError(
            f"No video in playlist {url} has usable captions "
            f"({len(skipped)} skipped).\n"
            "v1 needs manual or auto captions; Whisper transcription "
            "is not supported yet."
        )

    full_text = "".join(chunks)
    words = len(full_text.split())
    metadata = {
        "source_type": "playlist",
        "title": title,
        "origin": info.get("webpage_url") or url,
        "channel": info.get("channel") or info.get("uploader"),
        "video_count": len(entries),
        "skipped": skipped,
        "words": words,
        "est_tokens": utils.estimate_tokens(words),
        "segments": segments,
    }
    return full_text, metadata
