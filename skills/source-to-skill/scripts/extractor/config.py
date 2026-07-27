"""Static configuration: supported sources, paths, optional dependencies."""
import tempfile
from pathlib import Path

WORK_DIR_NAME = "source_skill_work"

# Valid values for --type / detect_source's forced parameter.
SOURCE_TYPES = ("youtube", "playlist", "paper", "book", "article", "repo")

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

# Modern arXiv ids only (e.g. 1706.03762, 2406.01234v2).
ARXIV_URL_PATTERN = (
    r"(?:https?://)?(?:www\.)?arxiv\.org/(?:abs|pdf)/"
    r"(?P<arxiv_id>\d{4}\.\d{4,5}(?:v\d+)?)"
)

# Segment window (seconds) for videos without chapters.
DEFAULT_SEGMENT_WINDOW_S = 600

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

# Timeout (seconds) for network fetches: article pages, caption files,
# repo tarballs. Without it a stalled server hangs the CLI forever.
FETCH_TIMEOUT_S = 30

OPTIONAL_DEPS = {
    "yt_dlp": {"pip": "yt-dlp", "needed_for": "YouTube videos"},
    "fitz": {"pip": "PyMuPDF", "needed_for": "PDF papers and books"},
}


def work_dir() -> Path:
    return Path(tempfile.gettempdir()) / WORK_DIR_NAME
