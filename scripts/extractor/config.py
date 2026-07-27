"""Static configuration: supported sources, paths, optional dependencies."""
import tempfile
from pathlib import Path

WORK_DIR_NAME = "source_skill_work"

YOUTUBE_URL_PATTERNS = (
    r"(?:https?://)?(?:www\.|m\.|music\.)?youtube\.com/watch\?",
    r"(?:https?://)?youtu\.be/",
    r"(?:https?://)?(?:www\.|m\.|music\.)?youtube\.com/shorts/",
    r"(?:https?://)?(?:www\.|m\.|music\.)?youtube\.com/live/",
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

OPTIONAL_DEPS = {
    "yt_dlp": {"pip": "yt-dlp", "needed_for": "YouTube videos"},
    "fitz": {"pip": "PyMuPDF", "needed_for": "PDF papers"},
}


def work_dir() -> Path:
    return Path(tempfile.gettempdir()) / WORK_DIR_NAME
