"""Academic paper parser: PyMuPDF text extraction + section heuristics."""
import collections
import datetime
import http.client
import re
import shutil
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
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
    r"^(?:(\d{1,2})\.?\s+)?(" + "|".join(SECTION_HEADINGS) + r")\s*$",
    re.IGNORECASE,
)
REFERENCE_HEADINGS = ("references", "bibliography")

# "3 Model Architecture", "3. Experiments" (top-level only: "3.1 X" never
# matches because the dot is followed by a digit, not whitespace).
NUMBERED_RE = re.compile(r"^(\d{1,2})\.?\s+(\S.*)$")
# Section number alone on its line; PyMuPDF puts the title on the next one.
NUMBER_ONLY_RE = re.compile(r"^(\d{1,2})\.?$")
LETTERED_RE = re.compile(r"^([A-H])(?:[.:])?\s+(\S.*)$")
LETTER_ONLY_RE = re.compile(r"^([A-H])\.?$")
APPENDIX_RE = re.compile(
    r"^(?:Appendix|Appendices|Supplementary Material)"
    r"(?:\s+([A-Z])\b)?\s*[:.\-–—]?\s*(.*)$"
)
BARE_NUMBER_RE = re.compile(r"^\d{1,4}$")
DOT_LEADERS_RE = re.compile(r"(?:\.\s?){4,}")
MAX_SECTION_NUMBER = 20
MAX_HEADING_CHARS = 80
MAX_HEADING_WORDS = 12
# A numbered heading may skip at most this many numbers (a missed section);
# larger jumps are table cells and page numbers.
MAX_SECTION_JUMP = 3


def _norm(text: str) -> str:
    return " ".join(text.split())


def _is_title(text: str) -> bool:
    """Short, capitalized, non-sentence, non-table text."""
    if not 2 <= len(text) <= MAX_HEADING_CHARS:
        return False
    if not text[0].isalpha() or not text[0].isupper():
        return False
    if text[-1] in ".,;" or DOT_LEADERS_RE.search(text):
        return False
    words = text.split()
    if len(words) > MAX_HEADING_WORDS:
        return False
    return not any(re.fullmatch(r"[\d.,%()\-+]+", word) for word in words)


def _is_toc_entry(lines: list[str], next_index: int) -> bool:
    """Table-of-contents entries are followed by a bare page number."""
    return next_index < len(lines) and bool(BARE_NUMBER_RE.match(lines[next_index]))


def _numbered_candidate(lines, i):
    """(number, title, lines consumed) for a numbered heading at line i."""
    line = lines[i]
    match = NUMBER_ONLY_RE.match(line)
    if match and i + 1 < len(lines):
        return int(match.group(1)), lines[i + 1], 2
    match = NUMBERED_RE.match(line)
    if match:
        return int(match.group(1)), match.group(2), 1
    return None


def _lettered_candidate(lines, i):
    line = lines[i]
    match = LETTER_ONLY_RE.match(line)
    if match and i + 1 < len(lines):
        return match.group(1), lines[i + 1], 2
    match = LETTERED_RE.match(line)
    if match:
        return match.group(1), match.group(2), 1
    return None


def detect_sections(text: str, font_headings=None) -> list[dict]:
    """[{'title', 'offset'}] for top-level headings; never empty.

    Recognizes the named headings in SECTION_HEADINGS, numbered top-level
    sections ("3 Model Architecture", or "3" and the title on separate
    lines), and appendices ("A Title", "Appendix B: Title"). Subsections stay
    inside their parent. After the references only appendix headings start
    new segments. `font_headings` (normalized line texts set in a larger
    font, see `_font_profile`) marks unlettered appendix headings there.
    """
    font_headings = font_headings or set()
    raw_lines = text.splitlines(keepends=True)
    lines = [line.strip() for line in raw_lines]
    starts = []
    offset = 0
    for line in raw_lines:
        starts.append(offset)
        offset += len(line)

    sections = []
    last_number = 0
    last_letter = "@"  # chr(ord("A") - 1)
    after_references = False
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line:
            i += 1
            continue
        found = None  # (title, lines consumed, kind)

        appendix = APPENDIX_RE.match(line)
        if appendix:
            letter, rest = appendix.group(1), appendix.group(2).strip()
            # "...detailed in\nAppendix C." is a wrapped sentence, not a heading.
            prose_wrap = not rest and line.endswith(".")
            if (
                not prose_wrap
                and (not rest or _is_title(rest))
                and not _is_toc_entry(lines, i + 1)
            ):
                label = "Appendix" + (f" {letter}" if letter else "")
                found = (f"{label}: {rest}" if rest else label, 1, "appendix")
                if letter and letter <= "H":
                    last_letter = max(last_letter, letter)

        if found is None and not after_references:
            named = HEADING_RE.match(line)
            if named and not _is_toc_entry(lines, i + 1):
                found = (named.group(2).title(), 1, "named")
                if named.group(1):
                    last_number = max(last_number, int(named.group(1)))

        if found is None and not after_references:
            numbered = _numbered_candidate(lines, i)
            if numbered:
                number, title, used = numbered
                if (
                    last_number < number <= last_number + MAX_SECTION_JUMP
                    and number <= MAX_SECTION_NUMBER
                    and _is_title(title)
                    and not _is_toc_entry(lines, i + used)
                ):
                    found = (title, used, "numbered")
                    last_number = number

        if found is None and (last_number or after_references):
            lettered = _lettered_candidate(lines, i)
            if lettered:
                letter, title, used = lettered
                if (
                    ord(last_letter) < ord(letter) <= ord(last_letter) + 2
                    and _is_title(title)
                    and _title_case(title)
                    and not _is_toc_entry(lines, i + used)
                ):
                    found = (f"Appendix {letter}: {title}", used, "appendix")
                    last_letter = letter

        if (
            found is None
            and after_references
            and _norm(line) in font_headings
            and _is_title(line)
        ):
            found = (f"Appendix: {_norm(line)}", 1, "appendix")

        if found is None and after_references:
            named = HEADING_RE.match(line)
            if named and named.group(2).lower() in REFERENCE_HEADINGS:
                found = (named.group(2).title(), 1, "named")

        if found:
            title, used, kind = found
            sections.append({"title": title, "offset": starts[i]})
            if kind == "named" and title.lower() in REFERENCE_HEADINGS:
                after_references = True
            i += used
        else:
            i += 1
    if not sections:
        sections = [{"title": "Full text", "offset": 0}]
    return sections


SMALL_WORDS = {
    "a", "an", "and", "as", "at", "by", "for", "from", "in", "of", "on",
    "or", "the", "to", "with", "via", "vs", "vs.",
}


def _title_case(text: str) -> bool:
    """Appendix titles are Title Case; prose lines starting with "A" are not."""
    words = [w for w in text.split() if w[0].isalpha()]
    return all(w[0].isupper() or w.lower() in SMALL_WORDS for w in words)


DOI_RE = re.compile(r"\b10\.\d{4,9}/[^\s]+")
YEAR_RE = re.compile(r"\b(?:19|20)\d{2}\b")
# Punctuation that commonly trails a DOI in prose but is not part of it.
DOI_TRAILING_CHARS = ".,;:)]}\"'"

VENUES = (
    "NIPS", "NeurIPS", "ICML", "ICLR", "CVPR", "ICCV", "ECCV", "ACL",
    "EMNLP", "NAACL", "EACL", "COLING", "AAAI", "IJCAI", "KDD", "SIGIR",
    "WWW", "AISTATS", "UAI", "COLT", "TACL", "JMLR", "CHI", "SIGGRAPH",
    "ICRA", "IROS", "RSS", "CoRL", "INTERSPEECH", "ICASSP", "WACV", "BMVC",
    "MICCAI", "WSDM", "CIKM", "RecSys", "OSDI", "SOSP", "NSDI", "USENIX",
)
VENUE_RE = re.compile(
    r"\b(?:" + "|".join(VENUES) + r")\s*(?:['’](\d{2})|((?:19|20)\d{2}))\b"
)
CONFERENCE_RE = re.compile(
    r"\b(?:Conference|Proceedings|Symposium|Workshop)\b[^\n]{0,150}?"
    r"\b((?:19|20)\d{2})\b"
)
# arXiv side stamp on page 1: "arXiv:1706.03762v7  [cs.CL]  2 Aug 2023".
ARXIV_STAMP_RE = re.compile(
    r"\barXiv:(\d{4}\.\d{4,5}|[a-z\-]+(?:\.[A-Z]{2})?/\d{7})(?:v\d+)?"
    r"\s+\[[\w.\-]+\]"
)
ARXIV_API_URL = "https://export.arxiv.org/api/query"
ATOM_NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "arxiv": "http://arxiv.org/schemas/atom",
}


def _warn(message: str) -> None:
    print(f"WARNING: {message}", file=sys.stderr)


def _plausible_year(year) -> bool:
    return year is not None and 1900 <= year <= datetime.date.today().year + 1


def _find_doi(text: str):
    match = DOI_RE.search(text)
    return match.group(0).rstrip(DOI_TRAILING_CHARS) if match else None


def _find_year(text: str):
    """First plausible year in prose; skips 2048-style numbers and, when any
    other year exists, years inside dataset names ("WMT 2014", "ImageNet
    2012": the preceding word has two or more capitals)."""
    dataset_year = None
    for match in YEAR_RE.finditer(text):
        year = int(match.group(0))
        if not _plausible_year(year):
            continue
        before = re.search(r"(\S+)\s+$", text[max(0, match.start() - 40):match.start()])
        if before and sum(c.isupper() for c in before.group(1)) >= 2:
            dataset_year = dataset_year or year
            continue
        return year
    return dataset_year


def year_from_arxiv_id(arxiv_id):
    """Submission year from the id's YYMM: 1706.03762 -> 2017."""
    if not arxiv_id:
        return None
    match = re.match(r"^(\d{2})(\d{2})\.\d{4,5}", arxiv_id)
    if match:
        return 2000 + int(match.group(1))
    match = re.search(r"/(\d{2})(\d{2})\d{3}", arxiv_id)
    if match:
        yy = int(match.group(1))
        return (1900 if yy >= 91 else 2000) + yy
    return None


def venue_year(text: str):
    """Year from a venue stamp ("NIPS 2017", "Conference on ... 2019")."""
    for match in VENUE_RE.finditer(text):
        year = (
            2000 + int(match.group(1)) if match.group(1) else int(match.group(2))
        )
        if _plausible_year(year):
            return year
    for match in CONFERENCE_RE.finditer(text):
        year = int(match.group(1))
        if _plausible_year(year):
            return year
    return None


def _creation_year(doc_meta: dict):
    match = re.match(r"^D:(\d{4})", doc_meta.get("creationDate") or "")
    year = int(match.group(1)) if match else None
    return year if _plausible_year(year) else None


def _resolve_year(api_year, arxiv_id, page1: str, doc_meta: dict):
    for year in (
        api_year,
        year_from_arxiv_id(arxiv_id),
        venue_year(page1),
        _creation_year(doc_meta),
        _find_year(page1),
    ):
        if _plausible_year(year):
            return year
    return None


def fetch_arxiv_metadata(arxiv_id: str):
    """Title/authors/year/doi from the arXiv API, or None (with a warning)."""
    url = f"{ARXIV_API_URL}?id_list={urllib.parse.quote(arxiv_id)}"
    try:
        with urllib.request.urlopen(url, timeout=config.FETCH_TIMEOUT_S) as response:
            data = response.read()
        root = ET.fromstring(data)
    except (OSError, ValueError, ET.ParseError, http.client.HTTPException) as err:
        _warn(
            f"could not fetch arXiv metadata for {arxiv_id} ({err}); "
            "falling back to PDF heuristics."
        )
        return None
    entry = root.find("atom:entry", ATOM_NS)
    entry_id = entry.findtext("atom:id", "", ATOM_NS) if entry is not None else ""
    title = _norm(entry.findtext("atom:title", "", ATOM_NS)) if entry is not None else ""
    if entry is None or "api/errors" in entry_id or not title:
        _warn(
            f"arXiv metadata for {arxiv_id} not found in the API response; "
            "falling back to PDF heuristics."
        )
        return None
    authors = [
        _norm(name.text or "")
        for name in entry.findall("atom:author/atom:name", ATOM_NS)
        if (name.text or "").strip()
    ]
    published = entry.findtext("atom:published", "", ATOM_NS)
    year = int(published[:4]) if re.match(r"^\d{4}", published) else None
    doi = _norm(entry.findtext("arxiv:doi", "", ATOM_NS)) or None
    return {
        "title": title,
        "authors": authors or None,
        "year": year if _plausible_year(year) else None,
        "doi": doi,
    }


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


def _font_lines(doc) -> list[tuple]:
    """[(page_index, font_size, text)] per text line, in reading order."""
    out = []
    for index, page in enumerate(doc):
        try:
            blocks = page.get_text("dict").get("blocks", [])
        except Exception:  # damaged page: skip font analysis for it
            continue
        for block in blocks:
            for line in block.get("lines", []):
                spans = [s for s in line.get("spans", []) if s.get("text", "").strip()]
                if spans:
                    text = _norm("".join(s["text"] for s in line["spans"]))
                    out.append((index, max(s["size"] for s in spans), text))
    return out


def _body_size(font_lines) -> float:
    weights = collections.Counter()
    for _, size, text in font_lines:
        weights[round(size)] += len(text)
    return weights.most_common(1)[0][0] if weights else 0.0


def _font_headings(font_lines, body: float) -> set:
    """Line texts set noticeably larger than body text (section headings)."""
    return {
        text
        for _, size, text in font_lines
        if body and size >= body + 1 and _is_title(text)
    }


def _title_from_fonts(font_lines, body: float):
    """Page-1 run of largest-font lines, skipping the arXiv side stamp."""
    candidates = [
        (size, text)
        for page, size, text in font_lines
        if page == 0
        and not text.lower().startswith("arxiv:")
        and sum(c.isalpha() for c in text) >= 3
    ]
    if not candidates:
        return None
    biggest = max(size for size, _ in candidates)
    if biggest < body + 1:
        return None
    parts = []
    for size, text in candidates:
        if abs(size - biggest) <= 0.5:
            parts.append(text)
        elif parts:
            break
    title = _norm(" ".join(parts)).rstrip("*∗†‡ ")
    return title[:300] or None


def _plausible_title(title, stem: str) -> bool:
    title = (title or "").strip()
    low = title.lower()
    if len(title) < 4 or title == stem:
        return False
    if low.startswith("untitled") or low in ("title", "none", "unknown"):
        return False
    if low.startswith("microsoft word") or low.startswith("microsoft powerpoint"):
        return False
    if re.search(r"\.(pdf|docx?|tex|dvi|ps|rtf|odt)$", low):
        return False
    return not (" " not in title and re.search(r"[_\-.\d]", title))


def _split_authors(author):
    """PDF metadata author string -> list (";" / " and " / "," separated)."""
    author = (author or "").strip()
    if not author:
        return None
    parts = [p for p in re.split(r"\s*;\s*|\s+and\s+|\s*&\s*", author) if p]
    if len(parts) == 1 and "," in author:
        comma_parts = [p.strip() for p in author.split(",") if p.strip()]
        # "Lovelace, Ada" is one name; "Ada Lovelace, Alan Turing" is two.
        if all(len(p.split()) >= 2 for p in comma_parts):
            parts = comma_parts
    return [p.strip() for p in parts if p.strip()] or None


REF_BRACKET_RE = re.compile(r"^\[(?:\d{1,3}|[A-Za-z][\w+\-]{0,15})\]")
REF_NUMBERED_RE = re.compile(r"^(\d{1,3})[.)]?\s+\S")


def _join_wrapped(entry: str, line: str) -> str:
    if not entry:
        return line
    if entry.endswith("-"):
        # "Convolu-" + "tional" is a line-break hyphen; "1-" + "10" is not.
        if len(entry) > 1 and entry[-2].isalpha() and line[:1].islower():
            return entry[:-1] + line
        return entry + line
    return entry + " " + line


def _split_references(lines: list[str]) -> list[str]:
    lines = [line for line in lines if line and not BARE_NUMBER_RE.match(line)]
    bracketed = any(REF_BRACKET_RE.match(line) for line in lines)
    numbered_starts = set()
    if not bracketed:
        expected = 1
        for index, line in enumerate(lines):
            match = REF_NUMBERED_RE.match(line)
            if match and int(match.group(1)) == expected:
                numbered_starts.add(index)
                expected += 1
    entries = []
    current = ""
    for index, line in enumerate(lines):
        if bracketed:
            starts = bool(REF_BRACKET_RE.match(line))
        elif numbered_starts:
            starts = index in numbered_starts
        else:
            # Unnumbered (author-year) lists: an entry ends with a period
            # and the next one starts with a capitalized surname.
            starts = not current or (current.endswith(".") and line[:1].isupper())
        if starts:
            if current:
                entries.append(current)
            current = line
        elif current:
            current = _join_wrapped(current, line)
        # Lines before the first marker (stray headers) are dropped.
    if current:
        entries.append(current)
    return [_norm(entry) for entry in entries]


def extract_references(full_text: str, sections: list[dict]) -> list[str]:
    for i, section in enumerate(sections):
        if section["title"].lower() in REFERENCE_HEADINGS:
            end = (
                sections[i + 1]["offset"]
                if i + 1 < len(sections)
                else len(full_text)
            )
            block = full_text[section["offset"]:end]
            return _split_references(
                [line.strip() for line in block.splitlines()[1:]]
            )
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
    page1 = page_texts[0] if page_texts else ""
    font_lines = _font_lines(doc)
    body = _body_size(font_lines)
    sections = detect_sections(full_text, _font_headings(font_lines, body))
    offsets = _page_offsets(page_texts)
    doc_meta = doc.metadata or {}

    url_match = re.match(config.ARXIV_URL_PATTERN, source)
    arxiv_id = url_match.group("arxiv_id") if url_match else None
    api = fetch_arxiv_metadata(arxiv_id) if arxiv_id else None
    if arxiv_id is None:
        stamp = ARXIV_STAMP_RE.search(page1)
        arxiv_id = stamp.group(1) if stamp else None
    api = api or {}

    stem = Path(path).stem
    title = api.get("title")
    if not title:
        meta_title = (doc_meta.get("title") or "").strip()
        if _plausible_title(meta_title, stem):
            title = meta_title
        else:
            title = _title_from_fonts(font_lines, body) or stem

    metadata = {
        "source_type": "paper",
        "title": title,
        "authors": api.get("authors") or _split_authors(doc_meta.get("author")),
        "year": _resolve_year(api.get("year"), arxiv_id, page1, doc_meta),
        "doi": api.get("doi") or _find_doi(full_text[:5000]),
        "arxiv_id": arxiv_id,
        "abstract_url": f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else None,
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
