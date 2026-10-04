"""Static configuration: supported sources, paths, optional dependencies."""
import tempfile
from pathlib import Path

WORK_DIR_NAME = "source_skill_work"

# Valid values for --type / detect_source's forced parameter.
SOURCE_TYPES = (
    "youtube", "playlist", "audio", "paper", "book", "article", "repo",
)

YOUTUBE_URL_PATTERNS = (
    r"(?:https?://)?(?:www\.|m\.|music\.)?youtube\.com/watch\?",
    r"(?:https?://)?youtu\.be/",
    r"(?:https?://)?(?:www\.|m\.|music\.)?youtube\.com/shorts/",
    r"(?:https?://)?(?:www\.|m\.|music\.)?youtube\.com/live/",
)

# Dedicated playlist pages only; watch?v=...&list=... stays a single video.
PLAYLIST_URL_PATTERN = (
    r"(?:https?://)?(?:www\.|m\.|music\.)?youtube\.com/playlist\?(?:[^#]*&)?list="
)

# Bare repo URLs only; deeper paths (/tree/..., /blob/...) are not repos.
# A query/fragment tail (?tab=readme-ov-file, #readme - GitHub's own UI
# appends these) is fine, and URLs are matched case-insensitively.
GITHUB_REPO_PATTERN = (
    r"(?i)(?:https?://)?(?:www\.)?github\.com/[A-Za-z0-9][A-Za-z0-9-]*/"
    r"[A-Za-z0-9._-]+/?(?:[?#].*)?$"
)

# Channel pages (@handle, /channel/UC..., /c/name, /user/name), with an
# optional tab (/videos, /streams, /featured, ...). They extract as
# playlists of the channel's uploads.
CHANNEL_URL_PATTERN = (
    r"(?i)(?:https?://)?(?:www\.|m\.)?youtube\.com/"
    r"(?P<channel>@[\w.-]+|channel/[\w-]+|c/[\w.-]+|user/[\w.-]+)"
    r"(?:/[\w-]*)?/?(?:[?#].*)?$"
)

# Channels extract only their latest uploads unless --limit says otherwise.
CHANNEL_DEFAULT_LIMIT = 20

# Podcast pages yt-dlp can download episodes from.
PODCAST_URL_PATTERNS = (
    r"(?i)(?:https?://)?podcasts\.apple\.com/",
)

# Audio/video file extensions: local files and direct media URLs.
MEDIA_EXTENSIONS = (
    ".mp3", ".m4a", ".m4b", ".aac", ".wav", ".flac", ".ogg", ".oga",
    ".opus", ".webm", ".mp4", ".m4v", ".mov", ".mkv",
)

# Modern arXiv ids only (e.g. 1706.03762, 2406.01234v2).
ARXIV_URL_PATTERN = (
    r"(?:https?://)?(?:www\.)?arxiv\.org/(?:abs|pdf)/"
    r"(?P<arxiv_id>\d{4}\.\d{4,5}(?:v\d+)?)"
)

# Segment window (seconds) for videos without chapters.
DEFAULT_SEGMENT_WINDOW_S = 600

# Inside a segment, prefix a cue with [t=Ns] at most this often (seconds).
INLINE_TIMESTAMP_EVERY_S = 60

# Rough words -> tokens factor for cost estimates.
TOKENS_PER_WORD = 1.333

# Below this word count a PDF is treated as having no text layer.
MIN_PDF_WORDS = 50

# Below this word count an extracted web page is not a readable article.
ARTICLE_MIN_WORDS = 100

# Cap on total text pulled from a GitHub repo's README + docs.
REPO_TEXT_CAP_BYTES = 2_000_000

# Playlists over this many videos get a stderr warning (still processed).
PLAYLIST_WARN_VIDEOS = 30

# A playlist stops after this many consecutive HTTP 429 responses.
RATE_LIMIT_ABORT_AFTER = 3

# Timeout (seconds) for network fetches: article pages, caption files,
# repo tarballs. Without it a stalled server hangs the CLI forever.
FETCH_TIMEOUT_S = 30

OPTIONAL_DEPS = {
    "yt_dlp": {
        "pip": "yt-dlp", "needed_for": "YouTube videos, podcasts, audio",
    },
    "fitz": {"pip": "PyMuPDF", "needed_for": "PDF papers and books"},
}

# Whisper backends for audio transcription, in order of preference.
# Default models balance speed and accuracy on a laptop; override with
# the SOURCE_TO_SKILL_WHISPER_MODEL environment variable.
WHISPER_BACKENDS = {
    "mlx_whisper": {
        "pip": "mlx-whisper",
        "model": "mlx-community/whisper-large-v3-turbo",
        "needs_ffmpeg": True,
    },
    "faster_whisper": {
        "pip": "faster-whisper",
        "model": "small",
        "needs_ffmpeg": False,
    },
    "whisper": {
        "pip": "openai-whisper",
        "model": "small",
        "needs_ffmpeg": True,
    },
}
WHISPER_MODEL_ENV = "SOURCE_TO_SKILL_WHISPER_MODEL"

# yt-dlp breaks as YouTube changes; --check warns past this age (days).
YT_DLP_STALE_DAYS = 60

_work_dir_override = None


def set_work_dir(path) -> None:
    """Point work_dir() at `path` for this run (None restores the default)."""
    global _work_dir_override
    _work_dir_override = Path(path) if path is not None else None


def work_dir() -> Path:
    if _work_dir_override is not None:
        return _work_dir_override
    return Path(tempfile.gettempdir()) / WORK_DIR_NAME
