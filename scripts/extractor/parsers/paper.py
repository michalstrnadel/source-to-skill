"""Academic paper parser: PyMuPDF text extraction + section heuristics."""
import datetime
import re
import shutil
import urllib.request
from pathlib import Path

from .. import config, dependencies, utils
from ..utils import ExtractError

SECTION_HEADINGS = (
    "abstract", "introduction", "background", "related work",
    "materials and methods", "methods", "methodology", "experiments",
    "results", "discussion", "limitations", "conclusions", "conclusion",
    "acknowledgments", "acknowledgements", "references", "bibliography",
    "appendix",
)

HEADING_RE = re.compile(
    r"^(?:\d+\.?\s+)?(" + "|".join(SECTION_HEADINGS) + r")\s*$",
    re.IGNORECASE,
)


def detect_sections(text: str) -> list[dict]:
    """[{'title', 'offset'}] for recognized headings; never empty."""
    sections = []
    offset = 0
    for line in text.splitlines(keepends=True):
        match = HEADING_RE.match(line.strip())
        if match:
            sections.append({"title": match.group(1).title(), "offset": offset})
        offset += len(line)
    if not sections:
        sections = [{"title": "Full text", "offset": 0}]
    return sections


DOI_RE = re.compile(r"\b10\.\d{4,9}/[^\s]+")
YEAR_RE = re.compile(r"\b(?:19|20)\d{2}\b")
# Punctuation that commonly trails a DOI in prose but is not part of it.
DOI_TRAILING_CHARS = ".,;:)]}\"'"


def _find_doi(text: str):
    match = DOI_RE.search(text)
    return match.group(0).rstrip(DOI_TRAILING_CHARS) if match else None


def _find_year(text: str):
    """First plausible publication year; skips numbers like 2048 (tokens)."""
    max_year = datetime.date.today().year + 1
    for match in YEAR_RE.finditer(text):
        year = int(match.group(0))
        if 1900 <= year <= max_year:
            return year
    return None


def _resolve(source: str) -> Path:
    """Return a local PDF path; downloads arXiv URLs into the work dir."""
    match = re.match(config.ARXIV_URL_PATTERN, source)
    if match:
        arxiv_id = match.group("arxiv_id")
        target = config.work_dir() / f"arxiv-{arxiv_id}.pdf"
        target.parent.mkdir(parents=True, exist_ok=True)
        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}"
        try:
            with urllib.request.urlopen(
                pdf_url, timeout=config.FETCH_TIMEOUT_S
            ) as response, open(target, "wb") as pdf_file:
                shutil.copyfileobj(response, pdf_file)
        except OSError as err:
            raise ExtractError(
                f"Failed to download {pdf_url}: {err}\n"
                "Check the arXiv id and your network, or save the PDF "
                "locally and pass its file path instead."
            ) from err
        return target
    if re.match(r"https?://", source):
        raise ExtractError(
            f"Unsupported paper URL: {source}\n"
            "Only arXiv URLs are downloaded automatically. Save the PDF "
            "locally and pass its file path instead."
        )
    path = Path(source).expanduser()
    if not path.is_file():
        raise ExtractError(f"PDF not found: {path}")
    return path


def _page_offsets(page_texts: list[str]) -> list[int]:
    offsets = []
    total = 0
    for text in page_texts:
        offsets.append(total)
        total += len(text) + 1  # +1 for the join newline
    return offsets


def _page_for_offset(offsets: list[int], offset: int) -> int:
    page = 1
    for i, start in enumerate(offsets, start=1):
        if offset >= start:
            page = i
    return page


def extract_references(full_text: str, sections: list[dict]) -> list[str]:
    for i, section in enumerate(sections):
        if section["title"].lower() in ("references", "bibliography"):
            end = (
                sections[i + 1]["offset"]
                if i + 1 < len(sections)
                else len(full_text)
            )
            block = full_text[section["offset"]:end]
            return [
                line.strip()
                for line in block.splitlines()[1:]
                if line.strip()
            ]
    return []


def parse(source: str):
    fitz = dependencies.require("fitz")
    path = _resolve(source)
    try:
        doc = fitz.open(path)
    except Exception as err:
        raise ExtractError(f"Cannot open PDF {path}: {err}") from err
    page_texts = [page.get_text() for page in doc]
    full_text = "\n".join(page_texts)
    words = len(full_text.split())
    if words < config.MIN_PDF_WORDS:
        raise ExtractError(
            f"{path} has no usable text layer (scanned PDF?).\n"
            "OCR is not supported yet - try an OCR'd copy of the paper."
        )
    sections = detect_sections(full_text)
    offsets = _page_offsets(page_texts)
    doc_meta = doc.metadata or {}
    metadata = {
        "source_type": "paper",
        "title": doc_meta.get("title") or Path(path).stem,
        "authors": doc_meta.get("author") or None,
        "year": _find_year(page_texts[0] if page_texts else ""),
        "doi": _find_doi(full_text[:5000]),
        "origin": source,
        "language": None,
        "page_count": doc.page_count,
        "words": words,
        "est_tokens": utils.estimate_tokens(words),
        "references": extract_references(full_text, sections),
        "segments": [
            {
                "title": section["title"],
                "start_s": None,
                "pages": _page_for_offset(offsets, section["offset"]),
                "offset": section["offset"],
            }
            for section in sections
        ],
    }
    doc.close()
    return full_text, metadata
