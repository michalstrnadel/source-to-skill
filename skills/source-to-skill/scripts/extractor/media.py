"""Audio download through yt-dlp (podcasts, media URLs, captionless video)."""
from pathlib import Path

from . import config
from .utils import ExtractError


def download_audio(ydl_mod, url: str):
    """Download the best audio-only stream; return (info, file path).

    No ffmpeg post-processing: the native container is kept and Whisper
    decodes it directly, so downloads work without ffmpeg installed.
    """
    target_dir = config.work_dir() / "media"
    target_dir.mkdir(parents=True, exist_ok=True)
    opts = {
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "noplaylist": True,
        "format": "bestaudio/best",
        "outtmpl": str(target_dir / "%(id)s.%(ext)s"),
    }
    with ydl_mod.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        if info.get("_type") == "playlist" and info.get("entries"):
            # A podcast show page resolves to its episodes; take the first.
            info = next(entry for entry in info["entries"] if entry)
        path = info.get("filepath") or (
            (info.get("requested_downloads") or [{}])[0].get("filepath")
        ) or ydl.prepare_filename(info)
    path = Path(path)
    if not path.is_file():
        raise ExtractError(
            f"Audio download from {url} produced no file.\n"
            "Retry, or download the audio yourself and pass the file path."
        )
    return info, path
