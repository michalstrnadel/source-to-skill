"""YouTube playlist parser: yt-dlp flat listing + per-video captions."""
import sys

import re

from .. import config, dependencies, transcribe as whisper, utils
from ..utils import ExtractError
from .audio import deep_link_template
from .youtube import _pick_track, marked_lines, video_cues


def _video_transcript(ydl_mod, video_url, force_transcribe=False):
    """Return (video info, transcript, captions kind) or raise.

    Captionless videos fall back to local Whisper when a backend is
    installed; otherwise they raise and the playlist skips them.
    """
    opts = {"quiet": True, "skip_download": True, "noplaylist": True}
    with ydl_mod.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(video_url, download=False)
    if not force_transcribe and whisper.available_backend() is None:
        if not _pick_track(info)[2]:
            raise ExtractError("no captions available")
    cues, _, captions = video_cues(
        ydl_mod, video_url, info, force_transcribe=force_transcribe
    )
    return info, "\n".join(marked_lines(cues)), captions


def _is_rate_limit(reason: str) -> bool:
    return "429" in reason or "Too Many Requests" in reason


def _rate_limit_message(url: str) -> str:
    return (
        f"YouTube is rate-limiting this machine (HTTP 429) while extracting "
        f"{url}.\nWait 10-30 minutes and retry; avoid running several "
        "YouTube extractions at once. Nothing was transcribed."
    )


def channel_videos_url(url: str) -> str:
    """A channel URL pointed at its uploads tab (/videos)."""
    match = re.match(config.CHANNEL_URL_PATTERN, url)
    base = url[: match.end("channel")]
    if not re.match(r"https?://", base):
        base = "https://" + base
    return base + "/videos"


def parse(url: str, limit=None, transcribe: bool = False):
    ydl_mod = dependencies.require("yt_dlp")
    is_channel = utils.is_channel_url(url)
    is_feed = utils.is_feed_url(url)
    listing_url = channel_videos_url(url) if is_channel else url
    if limit is None and (is_channel or is_feed):
        limit = (
            config.CHANNEL_DEFAULT_LIMIT if is_channel
            else config.FEED_DEFAULT_LIMIT
        )
        what = "videos" if is_channel else "episodes"
        print(
            f"NOTE: {'channel' if is_channel else 'podcast feed'} - "
            f"extracting the latest {limit} {what} "
            "(pass --limit N for more or fewer).",
            file=sys.stderr,
        )
    opts = {"quiet": True, "skip_download": True, "extract_flat": True}
    if limit is not None:
        opts["playlistend"] = limit
    with ydl_mod.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(listing_url, download=False)

    title = info.get("title") or "Untitled playlist"
    entries = [entry for entry in (info.get("entries") or []) if entry]
    if limit is not None:
        entries = entries[:limit]
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
    rate_limited_in_a_row = 0
    for number, entry in enumerate(entries, start=1):
        video_title = entry.get("title") or f"Video {number}"
        video_url = entry.get("url")
        if not video_url and entry.get("id") and not is_feed:
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
            video_info, transcript, captions = _video_transcript(
                ydl_mod, video_url, force_transcribe=transcribe
            )
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
            if _is_rate_limit(reason):
                rate_limited_in_a_row += 1
                if rate_limited_in_a_row >= config.RATE_LIMIT_ABORT_AFTER:
                    # Every further request deepens the block; stop now.
                    raise ExtractError(_rate_limit_message(url))
            else:
                rate_limited_in_a_row = 0
            continue
        rate_limited_in_a_row = 0
        if not is_feed:
            # Feed entries already carry the episode title; resolving the
            # enclosure URL only yields a file name.
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
                "captions": captions,
                "deep_link_template": deep_link_template(video_url),
            }
        )
        chunks.append(chunk)
        offset += len(chunk)

    if not chunks:
        if skipped and all(_is_rate_limit(s["reason"]) for s in skipped):
            raise ExtractError(_rate_limit_message(url))
        raise ExtractError(
            f"No video in playlist {url} has usable captions "
            f"({len(skipped)} skipped).\n"
            "Transcribe captionless videos locally: "
            + whisper.install_hint()
        )

    full_text = "".join(chunks)
    words = len(full_text.split())
    metadata = {
        "source_type": "playlist",
        "kind": (
            "channel" if is_channel else "feed" if is_feed else "playlist"
        ),
        "title": re.sub(r"\s+-\s+Videos$", "", title),
        "origin": info.get("webpage_url") or url,
        "channel": info.get("channel") or info.get("uploader"),
        "video_count": len(entries),
        "skipped": skipped,
        "words": words,
        "est_tokens": utils.estimate_tokens(words),
        "segments": segments,
    }
    return full_text, metadata
