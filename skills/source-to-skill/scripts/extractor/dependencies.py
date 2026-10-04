"""Optional-dependency probing and the `--check` report."""
import importlib
import shutil
from datetime import date

from . import config
from .utils import ExtractError


def probe() -> dict:
    report = {}
    for module, info in config.OPTIONAL_DEPS.items():
        try:
            importlib.import_module(module)
            available = True
        except ImportError:
            available = False
        report[module] = {"available": available, **info}
    return report


def require(module: str):
    """Import and return a module, or raise ExtractError with an install hint."""
    try:
        return importlib.import_module(module)
    except ImportError:
        info = config.OPTIONAL_DEPS.get(
            module, {"pip": module, "needed_for": "this source type"}
        )
        raise ExtractError(
            f"Missing dependency for {info['needed_for']}: {info['pip']}\n"
            f"Install it with: pip install {info['pip']}"
        ) from None


def yt_dlp_age_days(version: str, today=None):
    """Age in days of a date-based yt-dlp version (2026.08.19), or None."""
    parts = version.split(".")[:3]
    try:
        released = date(int(parts[0]), int(parts[1]), int(parts[2]))
    except (ValueError, IndexError):
        return None
    return ((today or date.today()) - released).days


def _yt_dlp_freshness():
    """A stale-version warning line for yt-dlp, or None."""
    try:
        version = importlib.import_module("yt_dlp.version").__version__
    except Exception:
        return None
    age = yt_dlp_age_days(version)
    if age is None or age <= config.YT_DLP_STALE_DAYS:
        return None
    return (
        f"WARN    yt-dlp {version} is {age} days old - YouTube changes often "
        "break old versions  -> pip install -U yt-dlp"
    )


def _transcription_lines():
    # Imported lazily: transcribe imports utils, which needs no deps.
    from . import transcribe

    backend = transcribe.available_backend()
    if backend is None:
        return [
            "MISSING Whisper (podcasts, audio files, captionless videos)"
            "  -> pip install mlx-whisper (Apple Silicon) or "
            "pip install faster-whisper"
        ]
    info = config.WHISPER_BACKENDS[backend]
    lines = [
        f"OK      {info['pip']} (podcasts, audio files, captionless videos;"
        f" model {transcribe.model_for(backend)})"
    ]
    if info["needs_ffmpeg"] and not shutil.which("ffmpeg"):
        lines.append(
            f"MISSING ffmpeg (needed by {info['pip']} to decode audio)"
            "  -> brew install ffmpeg / sudo apt install ffmpeg"
        )
    return lines


def check_report() -> str:
    lines = []
    for entry in probe().values():
        status = "OK     " if entry["available"] else "MISSING"
        hint = "" if entry["available"] else f"  -> pip install {entry['pip']}"
        lines.append(f"{status} {entry['pip']} ({entry['needed_for']}){hint}")
    stale = _yt_dlp_freshness()
    if stale:
        lines.append(stale)
    lines.extend(_transcription_lines())
    return "\n".join(lines)
