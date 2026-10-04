"""Book parser: EPUB via stdlib (zip + XML + HTMLParser), PDF via PyMuPDF."""
import posixpath
import re
import sys
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote
from xml.etree import ElementTree

from .. import config, dependencies, utils
from ..utils import ExtractError
from . import paper

CONTAINER_PATH = "META-INF/container.xml"
NCX_MEDIA_TYPE = "application/x-dtbncx+xml"

# Tags whose end (or self-close) marks a line break in the extracted text.
BLOCK_TAGS = {
    "p", "div", "section", "article", "h1", "h2", "h3", "h4", "h5", "h6",
    "li", "ul", "ol", "table", "tr", "td", "th", "blockquote", "figure",
    "figcaption", "header", "footer", "aside", "nav", "pre",
}
SKIP_TAGS = {"script", "style"}

# Marks a line inside <pre> whose indentation must survive text().
PRE_LINE = "\x01"

# Segment titles that are front matter rather than content; flagged in
# metadata so the generator can skip them (they are kept, not dropped -
# a License page is still worth a line in the skill).
FRONT_MATTER_RE = re.compile(
    r"^(table of contents|contents|contributors|dedications?|copyright"
    r"( page)?|title page|cover|index|list of (figures|tables))$",
    re.IGNORECASE,
)


class _ChapterText(HTMLParser):
    """Collects visible text plus the first <h1> and the <title>."""

    def __init__(self):
        super().__init__()
        self._parts = []
        self._skip = 0
        self._capture = None
        self._captured = []
        self.h1 = None
        self.title = None
        self._pre = 0

    def handle_starttag(self, tag, attrs):
        if tag in SKIP_TAGS:
            self._skip += 1
        elif tag == "pre":
            self._pre += 1
            self._parts.append("\n" + PRE_LINE)
        elif tag == "sup" and self._capture is None:
            # 2<sup>80</sup> must not collapse into "280".
            self._parts.append("^")
        elif tag == "br":
            self._parts.append("\n")
            if self._capture:
                self._captured.append(" ")
        elif tag == "h1" and self.h1 is None and self._capture is None:
            self._capture, self._captured = "h1", []
        elif tag == "title" and self.title is None and self._capture is None:
            self._capture, self._captured = "title", []

    def handle_endtag(self, tag):
        if tag in SKIP_TAGS and self._skip:
            self._skip -= 1
        if tag == "pre" and self._pre:
            self._pre -= 1
        if tag == self._capture:
            text = " ".join("".join(self._captured).split())
            if tag == "h1":
                self.h1 = text or None
            else:
                self.title = text or None
            self._capture = None
        if tag in BLOCK_TAGS:
            self._parts.append("\n")

    def handle_data(self, data):
        if self._skip:
            return
        if self._capture:
            self._captured.append(data)
        if self._capture != "title":
            if self._pre:
                # Code keeps its indentation: `git status -s` columns,
                # YAML, Python all change meaning without it.
                data = data.replace("\n", "\n" + PRE_LINE)
            self._parts.append(data)

    def text(self) -> str:
        raw = "".join(self._parts).replace("\u200b", "")
        lines = [
            line.replace(PRE_LINE, "").rstrip()
            if line.startswith(PRE_LINE)
            else line.replace(PRE_LINE, "").strip()
            for line in raw.splitlines()
        ]
        return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


class _NavToc(HTMLParser):
    """Collects (href, title) anchors from the toc <nav> of an EPUB3 nav doc."""

    def __init__(self):
        super().__init__()
        self.entries = []
        self._nav_types = []
        self._href = None
        self._text = []

    def _in_toc(self) -> bool:
        # epub:type is a space-separated property list; only a nav explicitly
        # typed "toc" is the table of contents.
        return bool(self._nav_types) and "toc" in self._nav_types[-1]

    def handle_starttag(self, tag, attrs):
        if tag == "nav":
            self._nav_types.append((dict(attrs).get("epub:type") or "").split())
        elif tag == "a" and self._in_toc():
            self._href = dict(attrs).get("href")
            self._text = []

    def handle_endtag(self, tag):
        if tag == "nav" and self._nav_types:
            self._nav_types.pop()
        elif tag == "a" and self._href is not None:
            title = " ".join("".join(self._text).split())
            if title:
                self.entries.append((self._href, title))
            self._href = None

    def handle_data(self, data):
        if self._href is not None:
            self._text.append(data)


def _chapter_text(xhtml: str):
    parser = _ChapterText()
    parser.feed(xhtml)
    parser.close()
    return parser.text(), parser.h1, parser.title


def _zip_path(base: str, href: str):
    """Resolve an href relative to `base` into a zip member path."""
    href = unquote(href.split("#", 1)[0])
    if not href:
        return None
    return posixpath.normpath(posixpath.join(base, href))


def _parse_xml(data: bytes, path: Path, what: str):
    try:
        return ElementTree.fromstring(data)
    except ElementTree.ParseError as err:
        raise ExtractError(
            f"{path}: cannot parse {what} ({err}).\n"
            "The EPUB is malformed - re-export it or try another copy."
        ) from err


def _dc(metadata_el, name: str) -> list:
    """All Dublin Core `name` values under the OPF <metadata> element."""
    if metadata_el is None:
        return []
    values = []
    for el in metadata_el.iter():
        if (el.tag == name or el.tag.endswith("}" + name)) and el.text:
            text = " ".join(el.text.split())
            if text:
                values.append(text)
    return values


def _ncx_titles(zf, ncx_path: str, path: Path) -> dict:
    """{zip path: chapter title} from toc.ncx navPoints (first wins)."""
    root = _parse_xml(zf.read(ncx_path), path, "toc.ncx")
    base = posixpath.dirname(ncx_path)
    titles = {}
    for nav_point in root.iter():
        if not nav_point.tag.endswith("}navPoint"):
            continue
        label = nav_point.find("./{*}navLabel/{*}text")
        content = nav_point.find("./{*}content")
        if label is None or content is None:
            continue
        title = " ".join((label.text or "").split())
        target = _zip_path(base, content.get("src") or "")
        if title and target:
            titles.setdefault(target, title)
    return titles


def _nav_titles(zf, nav_path: str) -> dict:
    """{zip path: chapter title} from an EPUB3 nav.xhtml toc (first wins)."""
    parser = _NavToc()
    parser.feed(zf.read(nav_path).decode("utf-8", "replace"))
    parser.close()
    base = posixpath.dirname(nav_path)
    titles = {}
    for href, title in parser.entries:
        target = _zip_path(base, href)
        if target:
            titles.setdefault(target, title)
    return titles


def _toc_titles(zf, names, opf, manifest, spine_el, opf_path, path: Path) -> dict:
    """Chapter titles from toc.ncx, else nav.xhtml, else empty."""
    base = posixpath.dirname(opf_path)
    ncx_id = spine_el.get("toc") if spine_el is not None else None
    ncx_item = manifest.get(ncx_id) or next(
        (
            item
            for item in manifest.values()
            if item["media_type"] == NCX_MEDIA_TYPE
            or item["href"].lower().endswith(".ncx")
        ),
        None,
    )
    if ncx_item:
        ncx_path = _zip_path(base, ncx_item["href"])
        if ncx_path in names:
            try:
                return _ncx_titles(zf, ncx_path, path)
            except ExtractError:
                # The NCX only supplies cosmetic titles - a malformed one
                # (e.g. HTML entities) must not abort the extraction; fall
                # through to nav.xhtml, then per-chapter heading fallbacks.
                pass
    nav_item = next(
        (
            item
            for item in manifest.values()
            if "nav" in item["properties"].split()
        ),
        None,
    )
    if nav_item:
        nav_path = _zip_path(base, nav_item["href"])
        if nav_path in names:
            return _nav_titles(zf, nav_path)
    return {}


def _parse_epub(path: Path, source: str):
    try:
        zf = zipfile.ZipFile(path)
    except (zipfile.BadZipFile, OSError) as err:
        raise ExtractError(
            f"{path} is not a valid EPUB (cannot read as zip: {err}).\n"
            "Check the file - it may be corrupted or a different format."
        ) from err
    with zf:
        names = set(zf.namelist())
        if CONTAINER_PATH not in names:
            raise ExtractError(
                f"{path} is missing {CONTAINER_PATH} - not a valid EPUB.\n"
                "Re-download or re-export the book and retry."
            )
        container = _parse_xml(zf.read(CONTAINER_PATH), path, "container.xml")
        rootfile = container.find(".//{*}rootfile")
        opf_path = rootfile.get("full-path") if rootfile is not None else None
        if not opf_path or opf_path not in names:
            raise ExtractError(
                f"{path}: container.xml does not point to a readable OPF "
                "package.\nThe EPUB is malformed - re-export it or try "
                "another copy."
            )
        opf = _parse_xml(zf.read(opf_path), path, "the OPF package")
        base = posixpath.dirname(opf_path)
        manifest = {
            item.get("id"): {
                "href": item.get("href") or "",
                "media_type": item.get("media-type") or "",
                "properties": item.get("properties") or "",
            }
            for item in opf.findall(".//{*}manifest/{*}item")
            if item.get("id")
        }
        spine_el = opf.find(".//{*}spine")
        idrefs = [
            ref.get("idref")
            for ref in (
                spine_el.findall("./{*}itemref") if spine_el is not None else []
            )
            if ref.get("idref")
        ]
        if not idrefs:
            raise ExtractError(
                f"{path} has an empty spine (no chapters to read).\n"
                "The EPUB is malformed - re-export it or try another copy."
            )
        titles = _toc_titles(zf, names, opf, manifest, spine_el, opf_path, path)
        chunks = []
        segments = []
        skipped = []
        offset = 0
        for number, idref in enumerate(idrefs, start=1):
            item = manifest.get(idref)
            if not item:
                skipped.append(idref)
                continue
            chapter_path = _zip_path(base, item["href"])
            if not chapter_path or chapter_path not in names:
                skipped.append(item["href"] or idref)
                continue
            xhtml = zf.read(chapter_path).decode("utf-8", "replace")
            text, h1, doc_title = _chapter_text(xhtml)
            title = (
                titles.get(chapter_path) or h1 or doc_title
                or f"Chapter {number}"
            )
            chunk = f"=== {title} ===\n{text}\n\n"
            segment = {
                "title": title, "start_s": None, "pages": None,
                "offset": offset,
            }
            if FRONT_MATTER_RE.match(title.strip()):
                segment["front_matter"] = True
            segments.append(segment)
            chunks.append(chunk)
            offset += len(chunk)
        if not chunks:
            raise ExtractError(
                f"{path}: no spine chapter file exists in the archive.\n"
                "The EPUB is malformed - re-export it or try another copy."
            )
        if skipped:
            print(
                f"WARNING: {path}: {len(skipped)} spine item(s) not found in "
                f"the EPUB and skipped: {', '.join(skipped)}.\n"
                "The extracted text may be incomplete.",
                file=sys.stderr,
            )
        metadata_el = opf.find(".//{*}metadata")
        dc_titles = _dc(metadata_el, "title")
        creators = _dc(metadata_el, "creator")
        languages = _dc(metadata_el, "language")
    full_text = "".join(chunks)
    words = len(full_text.split())
    metadata = {
        "source_type": "book",
        "title": dc_titles[0] if dc_titles else path.stem,
        "author": ", ".join(creators) if creators else None,
        "origin": source,
        "language": languages[0] if languages else None,
        "words": words,
        "est_tokens": utils.estimate_tokens(words),
        "segments": segments,
    }
    return full_text, metadata


def _parse_pdf(path: Path, source: str):
    fitz = dependencies.require("fitz")
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
            "OCR is not supported yet - try an OCR'd copy of the book."
        )
    offsets = paper._page_offsets(page_texts)
    # get_toc() reports page -1 for entries whose destination is not a page
    # in the document (external/web bookmarks, broken links) - skip them or
    # they would corrupt segment offsets. Over-range pages are clamped.
    outline = [
        (title, page)
        for level, title, page in (doc.get_toc() or [])
        if level == 1 and page >= 1
    ]
    if outline:
        segments = []
        for title, page in outline:
            page = min(page, doc.page_count)
            segments.append(
                {
                    "title": " ".join(title.split()) or "Untitled chapter",
                    "start_s": None,
                    "pages": page,
                    "offset": offsets[page - 1],
                }
            )
    else:
        segments = [
            {
                "title": section["title"],
                "start_s": None,
                "pages": paper._page_for_offset(offsets, section["offset"]),
                "offset": section["offset"],
            }
            for section in paper.detect_sections(full_text)
        ]
    doc_meta = doc.metadata or {}
    metadata = {
        "source_type": "book",
        "title": doc_meta.get("title") or path.stem,
        "author": doc_meta.get("author") or None,
        "origin": source,
        "language": None,
        "page_count": doc.page_count,
        "words": words,
        "est_tokens": utils.estimate_tokens(words),
        "segments": segments,
    }
    doc.close()
    return full_text, metadata


def parse(source: str):
    if re.match(r"https?://", source):
        raise ExtractError(
            f"Unsupported book URL: {source}\n"
            "Books are read from local files - download the EPUB or PDF "
            "and pass its path."
        )
    path = Path(source).expanduser()
    if not path.is_file():
        raise ExtractError(f"Book not found: {path}")
    suffix = path.suffix.lower()
    if suffix == ".epub":
        return _parse_epub(path, source)
    if suffix == ".pdf":
        return _parse_pdf(path, source)
    raise ExtractError(
        f"Unsupported book format: {path.name}\n"
        "Supported book formats: .epub, .pdf."
    )
