"""Web article parser: stdlib urllib fetch + HTMLParser content extraction."""
import json
import re
import urllib.error
import urllib.request
from html.parser import HTMLParser

from .. import config, utils
from ..utils import ExtractError

# Some sites serve error pages or block requests without a browser UA.
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

# Tags whose whole subtree is chrome/boilerplate, never article text.
# <template> holds inert, never-rendered markup (widget skeletons, dialogs).
DROP_TAGS = {
    "script", "style", "noscript", "svg", "nav", "header", "footer",
    "aside", "form", "template",
}

# Tags whose end (or self-close) marks a line break in the extracted text.
BLOCK_TAGS = {
    "p", "div", "section", "article", "main", "h1", "h2", "h3", "h4",
    "h5", "h6", "li", "ul", "ol", "table", "tr", "td", "th",
    "blockquote", "figure", "figcaption", "pre",
}

# Headings that become segment boundaries.
HEADING_TAGS = ("h1", "h2", "h3")

# Any h1-h6 end tag closes an open heading (HTML5 recovery for
# mismatched closes like <h2>Title</h3>).
ALL_HEADING_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6"}

AUTHOR_METAS = ("author", "article:author")
TWITTER_CREATOR = "twitter:creator"
DATE_METAS = (
    "article:published_time", "date", "publish-date", "publication-date",
    "dc.date",
)

# charset=<token> inside a Content-Type http-equiv content value.
CONTENT_CHARSET_RE = re.compile(
    r"charset\s*=\s*[\"']?([A-Za-z0-9][A-Za-z0-9._-]*)", re.IGNORECASE
)


# ---------------------------------------------------------------------------
# HTML rendering helpers shared with the EPUB parser (book.py).

# Table structure tags handled by TableRenderer rather than as plain blocks.
TABLE_TAGS = {"table", "thead", "tbody", "tfoot", "tr", "td", "th", "caption"}

# Inline formatting tags after which "Label:" gets a space when the source
# glued the next word on (<strong>Label:</strong>Text). Code-ish tags are
# deliberately absent: `std:</code>x` must stay verbatim.
LABEL_TAGS = {"strong", "b", "em", "i", "u", "span", "a", "label", "mark"}

FIGURE_PREFIX = "[figure] "

_COLLAPSE_RE = re.compile(r"[\s\x00-\x1f]+")
_BLANK_LINES_RE = re.compile(r"\n[ \t]*(?:\n[ \t]*)+")


def image_marker(attrs: dict):
    """`[image: alt]` for a meaningful <img>, None for decorative ones."""
    alt = " ".join((attrs.get("alt") or "").split())
    if not alt:
        return None
    for dim in ("width", "height"):
        if (attrs.get(dim) or "").strip().lower() in ("0", "1", "0px", "1px"):
            return None  # tracking pixel
    return f"[image: {alt}]"


class _Nested:
    """A rendered inner table sitting inside an outer table cell."""

    def __init__(self, lines, flat):
        self.lines, self.flat = lines, flat


class TableRenderer:
    """Renders <table> markup as Markdown-style pipe rows.

    Feed it start/end tags and text while `active`; when the outermost
    table closes, `end` returns the rendered block. Cell text is
    whitespace-collapsed (block breaks inside a cell become spaces); a
    `| --- |` separator follows a first row made of <th> cells or taken
    from <thead>. Inner tables are flattened into their cell. A
    single-column table is a layout wrapper, not data: its cells come
    back as plain lines with their block breaks intact.
    """

    def __init__(self):
        self._stack = []

    @property
    def active(self) -> bool:
        return bool(self._stack)

    def start(self, tag):
        if tag == "table":
            self._stack.append(
                {"rows": [], "row": None, "cell": None, "head": False,
                 "stray": []}
            )
            return
        table = self._stack[-1]
        if tag == "thead":
            table["head"] = True
        elif tag in ("tbody", "tfoot"):
            table["head"] = False
        elif tag == "tr":
            self._close_row(table)
            table["row"] = {"cells": [], "head": table["head"]}
        elif tag in ("td", "th"):
            self._close_cell(table)
            if table["row"] is None:
                table["row"] = {"cells": [], "head": table["head"]}
            table["cell"] = {"parts": [], "th": tag == "th"}

    def end(self, tag):
        """Return the rendered text when the outermost table closes."""
        table = self._stack[-1]
        if tag == "thead":
            table["head"] = False
        elif tag in ("td", "th"):
            self._close_cell(table)
        elif tag == "tr":
            self._close_row(table)
        elif tag == "table":
            return self._close_table()
        return None

    def data(self, text):
        table = self._stack[-1]
        if table["cell"] is not None:
            table["cell"]["parts"].append(text)
        else:
            table["stray"].append(text)  # <caption>, inter-tag text

    def flush(self):
        """Close any tables left open at EOF; return their rendering."""
        out = None
        while self._stack:
            out = self._close_table()
        return out

    @staticmethod
    def _close_cell(table):
        cell, table["cell"] = table["cell"], None
        if cell is None:
            return
        if table["row"] is None:
            table["row"] = {"cells": [], "head": table["head"]}
        table["row"]["cells"].append(cell)

    def _close_row(self, table):
        self._close_cell(table)
        row, table["row"] = table["row"], None
        if row and row["cells"]:
            table["rows"].append(row)

    @staticmethod
    def _flat(parts) -> str:
        text = "".join(p.flat if isinstance(p, _Nested) else p for p in parts)
        return _COLLAPSE_RE.sub(" ", text).strip()

    @staticmethod
    def _raw(parts) -> str:
        return "".join(
            "\n" + "\n".join(p.lines) + "\n" if isinstance(p, _Nested) else p
            for p in parts
        )

    def _close_table(self):
        table = self._stack.pop()
        self._close_row(table)
        rows = [
            row for row in table["rows"]
            if any(self._flat(c["parts"]) for c in row["cells"])
        ]
        caption = self._flat(table["stray"])
        filled = [
            [c for c in row["cells"] if self._flat(c["parts"])] for row in rows
        ]
        if all(len(cells) <= 1 for cells in filled):
            # Layout table (one column, or one filled cell per row next to
            # spacer/image cells): keep its content as ordinary text.
            lines = [caption] if caption else []
            lines += [
                _BLANK_LINES_RE.sub("\n", self._raw(cells[0]["parts"]))
                .strip("\n")
                for cells in filled
            ]
        else:
            lines = [caption] if caption else []
            for index, row in enumerate(rows):
                cells = [
                    self._flat(c["parts"]).replace("|", "\\|")
                    for c in row["cells"]
                ]
                lines.append("| " + " | ".join(cells) + " |")
                if index == 0 and (
                    row["head"] or all(c["th"] for c in row["cells"])
                ):
                    lines.append("| " + " | ".join(["---"] * len(cells)) + " |")
        if self._stack:
            flat = " ".join(
                self._flat(c["parts"]) for row in rows for c in row["cells"]
            )
            flat = " ".join(filter(None, [caption, flat]))
            self.data(_Nested(lines, f" {flat} "))
            return None
        return "\n".join(lines) + "\n" if lines else ""


class InlineMarkers:
    """Figcaption prefix and the bold-label space, applied to text data.

    Mixed into an HTMLParser subclass; call `_markers_start(tag)` /
    `_markers_end(tag)` from the tag handlers and pass every text chunk
    through `_markers_data(data)` before routing it.
    """

    def _markers_reset(self):
        self._caption_pending = False
        self._label_space = False
        self._last_data = ""

    def _markers_start(self, tag):
        if tag == "figcaption":
            self._caption_pending = True
        if tag not in LABEL_TAGS:
            self._label_space = False

    def _markers_end(self, tag):
        if tag == "figcaption":
            self._caption_pending = False
        self._label_space = tag in LABEL_TAGS and self._last_data.endswith(":")

    def _markers_data(self, data: str) -> str:
        if not data:
            return data
        if self._label_space and data[0].isalpha():
            data = " " + data
        self._label_space = False
        if self._caption_pending and data.strip():
            data = FIGURE_PREFIX + data.lstrip()
            self._caption_pending = False
        self._last_data = data
        return data


def _ld_names(value, ids) -> list:
    """Author names from a JSON-LD author value (str, dict, list, @id ref)."""
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [name for item in value for name in _ld_names(item, ids)]
    if isinstance(value, dict):
        name = value.get("name")
        if not isinstance(name, str) and isinstance(value.get("@id"), str):
            name = ids.get(value["@id"], {}).get("name")
        return [name] if isinstance(name, str) else []
    return []


def json_ld_meta(raw: str):
    """(author, datePublished) from one JSON-LD script body; never raises."""
    try:
        data = json.loads(raw)
    except (ValueError, RecursionError):
        return None, None
    nodes = data if isinstance(data, list) else [data]
    flat = []
    for node in nodes:
        if isinstance(node, dict):
            flat.append(node)
            graph = node.get("@graph")
            if isinstance(graph, list):
                flat.extend(n for n in graph if isinstance(n, dict))
    ids = {n["@id"]: n for n in flat if isinstance(n.get("@id"), str)}
    author = date = None
    for node in flat:
        if author is None and "author" in node:
            names = [
                " ".join(n.split()) for n in _ld_names(node["author"], ids)
            ]
            author = ", ".join(n for n in names if n) or None
        if date is None and isinstance(node.get("datePublished"), str):
            date = node["datePublished"].strip() or None
    return author, date


def _fetch(url: str):
    """Return (raw bytes, charset from the Content-Type header or None)."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(
            request, timeout=config.FETCH_TIMEOUT_S
        ) as response:
            return response.read(), response.headers.get_content_charset()
    except urllib.error.HTTPError as err:
        raise ExtractError(
            f"Cannot fetch article: {url} returned HTTP {err.code}.\n"
            "Open the URL in a browser to check it - the page may be gone, "
            "private, or blocking non-browser requests."
        ) from err
    except (urllib.error.URLError, OSError) as err:
        raise ExtractError(
            f"Cannot fetch article {url} ({err}).\n"
            "Check the URL and your network connection, then retry."
        ) from err


class _MetaCharset(HTMLParser):
    """Meta charset sniffer in the spirit of the HTML5 encoding prescan.

    Only a real charset declaration counts: a charset attribute
    (<meta charset=...>) or a Content-Type http-equiv content value.
    "charset=" appearing inside some other attribute's value (say a meta
    description) is ignored, as browsers ignore it.
    """

    def __init__(self):
        super().__init__()
        self.charset = None

    def handle_starttag(self, tag, attrs):
        if tag != "meta" or self.charset is not None:
            return
        attrs = dict(attrs)
        charset = (attrs.get("charset") or "").strip()
        if not charset:
            if (attrs.get("http-equiv") or "").lower() != "content-type":
                return
            match = CONTENT_CHARSET_RE.search(attrs.get("content") or "")
            charset = match.group(1) if match else ""
        self.charset = charset or None


def _meta_charset(raw: bytes):
    """Charset declared by a meta tag, or None."""
    scanner = _MetaCharset()
    # latin-1 decodes any byte, keeping the ASCII markup intact to scan.
    scanner.feed(raw.decode("latin-1"))
    scanner.close()
    return scanner.charset


def _decode(raw: bytes, header_charset) -> str:
    """Decode with the HTTP header charset, else meta charset, else UTF-8."""
    for charset in (header_charset, _meta_charset(raw), "utf-8"):
        if not charset:
            continue
        try:
            return raw.decode(charset)
        except (LookupError, UnicodeDecodeError):
            continue
    return raw.decode("utf-8", "replace")


class _PageText(InlineMarkers, HTMLParser):
    """Collects text, headings, and page metadata from an HTML document.

    Each text/heading item is tagged with whether it sits inside <article>
    or <main>, so the caller can prefer article > main > body content.
    Entity references are decoded by HTMLParser (convert_charrefs).
    """

    def __init__(self):
        super().__init__()
        self.items = []  # ("text"|"heading", payload, in_article, in_main)
        self.title = None
        self.og_title = None
        self.author = None
        self.date = None
        self.language = None
        self.time_date = None
        self._drop = 0
        self._article = 0
        self._main = 0
        self._capture = None
        self._captured = []
        self.ld_author = None
        self.ld_date = None
        self.twitter_creator = None
        self.rel_author = None
        self._ld_json = None  # buffer while inside an ld+json <script>
        self._rel_capture = None  # buffer while inside <a rel="author">
        self._table = TableRenderer()
        self._markers_reset()

    def _emit(self, kind, payload):
        self.items.append((kind, payload, self._article > 0, self._main > 0))

    def _line_start(self):
        """Emit a newline unless the output already sits at a line start."""
        if self.items and not self.items[-1][1].endswith("\n"):
            self._emit("text", "\n")

    def _text(self, text):
        """Route body text into the open table, else emit it."""
        if self._table.active:
            self._table.data(text)
        else:
            self._emit("text", text)

    def _flush_capture(self):
        tag, self._capture = self._capture, None
        text = " ".join("".join(self._captured).split())
        self._captured = []
        if tag == "title":
            self.title = text or None
        elif text:
            self._emit("heading", text)

    def _handle_meta(self, attrs):
        name = (attrs.get("name") or attrs.get("property") or "").lower()
        content = " ".join((attrs.get("content") or "").split())
        if not name or not content:
            return
        if name == "og:title":
            self.og_title = self.og_title or content
        elif name in AUTHOR_METAS:
            self.author = self.author or content
        elif name == TWITTER_CREATOR:
            self.twitter_creator = self.twitter_creator or content
        elif name in DATE_METAS:
            self.date = self.date or content

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        # Byline metadata is read even inside dropped chrome (<header>).
        if tag == "script" and "ld+json" in (attrs.get("type") or "").lower():
            self._ld_json = []
        elif (
            tag == "a"
            and self.rel_author is None
            and "author" in (attrs.get("rel") or "").lower().split()
        ):
            self._rel_capture = []
        if tag in DROP_TAGS:
            self._drop += 1
            return
        if self._drop:
            return
        self._markers_start(tag)
        if self._table.active and tag in TABLE_TAGS:
            self._table.start(tag)
            return
        if tag == "table":
            self._line_start()
            self._table.start(tag)
            return
        if self._table.active:
            # Inside a table everything is cell text: no headings, and a
            # block break is only a separator the renderer may collapse.
            if tag in BLOCK_TAGS:
                self._table.data("\n")
            elif tag == "br":
                self._table.data("\n")
            elif tag == "img":
                marker = image_marker(attrs)
                if marker:
                    self._table.data(f"\n{marker}\n")
            elif tag == "meta":
                self._handle_meta(attrs)
            return
        if self._capture is not None and tag in BLOCK_TAGS:
            # Unclosed <hN>/<title> recovery: browsers auto-close an open
            # heading when the next block element starts; without this the
            # rest of the page would be swallowed into the heading buffer.
            self._flush_capture()
        if (
            tag in BLOCK_TAGS
            and self._capture is None
            and self.items
            and self.items[-1][0] == "text"
            and not self.items[-1][1].endswith("\n")
        ):
            # A block opening mid-line (<li><b>Label</b>:<ul>...) starts a
            # new line; without this its text glues onto the label.
            self._emit("text", "\n")
        if tag == "meta":
            self._handle_meta(attrs)
        elif tag == "html":
            self.language = self.language or attrs.get("lang") or None
        elif tag == "time" and attrs.get("datetime"):
            # Fallback only: meta tags (handled above) win when present.
            self.time_date = self.time_date or attrs["datetime"].strip()
        elif tag == "article":
            self._article += 1
        elif tag == "main":
            self._main += 1
        elif tag == "br":
            if self._capture:
                self._captured.append(" ")
            else:
                self._emit("text", "\n")
        elif tag == "img" and self._capture is None:
            marker = image_marker(attrs)
            if marker:
                self._line_start()
                self._emit("text", f"{marker}\n")
        elif tag in HEADING_TAGS and self._capture is None:
            self._capture, self._captured = tag, []
        elif tag == "title" and self.title is None and self._capture is None:
            self._capture, self._captured = "title", []

    def handle_endtag(self, tag):
        if tag == "script" and self._ld_json is not None:
            author, date = json_ld_meta("".join(self._ld_json))
            self.ld_author = self.ld_author or author
            self.ld_date = self.ld_date or date
            self._ld_json = None
        elif tag == "a" and self._rel_capture is not None:
            self.rel_author = " ".join("".join(self._rel_capture).split()) or None
            self._rel_capture = None
        if tag in DROP_TAGS:
            if self._drop:
                self._drop -= 1
            return
        if self._drop:
            return
        self._markers_end(tag)
        if self._table.active:
            if tag in TABLE_TAGS:
                rendered = self._table.end(tag)
                if rendered:
                    self._emit("text", rendered)
            elif tag in BLOCK_TAGS:
                self._table.data("\n")
            if tag == "article" and self._article:
                self._article -= 1
            elif tag == "main" and self._main:
                self._main -= 1
            return
        if self._capture is not None and (
            tag == self._capture
            or (self._capture != "title" and tag in ALL_HEADING_TAGS)
        ):
            self._flush_capture()
        if tag == "article" and self._article:
            self._article -= 1
        elif tag == "main" and self._main:
            self._main -= 1
        if tag in BLOCK_TAGS:
            self._emit("text", "\n")

    def handle_data(self, data):
        if self._ld_json is not None:
            self._ld_json.append(data)
            return
        if self._rel_capture is not None:
            self._rel_capture.append(data)
        if self._drop:
            return
        data = self._markers_data(data)
        if self._capture is not None:
            self._captured.append(data)
        elif data:
            self._text(data)

    def close(self):
        super().close()
        if self._capture is not None:  # heading still open at EOF
            self._flush_capture()
        rendered = self._table.flush()
        if rendered:
            self._line_start()
            self._emit("text", rendered)


def _has_content(items) -> bool:
    return any(
        kind == "heading" or payload.strip()
        for kind, payload, _, _ in items
    )


def _scoped_items(items):
    """Prefer content inside <article>, then <main>, then the whole body."""
    for index in (2, 3):  # in_article flag, then in_main flag
        scoped = [item for item in items if item[index]]
        if _has_content(scoped):
            return scoped
    return items


def _clean(parts) -> str:
    lines = [line.strip() for line in "".join(parts).splitlines()]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def _sections(items):
    """[(heading title or None, cleaned text)] split at h1/h2/h3 items.

    Only the first section can be untitled (text before the first heading);
    it is dropped when empty.
    """
    sections = []
    title, parts = None, []
    for kind, payload, _, _ in items:
        if kind == "heading":
            sections.append((title, _clean(parts)))
            title, parts = payload, []
        else:
            parts.append(payload)
    sections.append((title, _clean(parts)))
    if len(sections) > 1 and sections[0] == (None, ""):
        sections = sections[1:]
    return sections


def parse(source: str):
    raw, header_charset = _fetch(source)
    page = _PageText()
    page.feed(_decode(raw, header_charset))
    page.close()
    sections = _sections(_scoped_items(page.items))
    content_words = sum(
        len((title or "").split()) + len(text.split())
        for title, text in sections
    )
    if content_words < config.ARTICLE_MIN_WORDS:
        raise ExtractError(
            f"Couldn't extract a readable article from {source} "
            f"({content_words} words found, need "
            f"{config.ARTICLE_MIN_WORDS}).\n"
            "The page may render its text with JavaScript or require a "
            "login - save it as a PDF and pass the file, or try another URL."
        )
    chunks = []
    segments = []
    offset = 0
    for title, text in sections:
        if title is None:
            title = "Full text" if len(sections) == 1 else "Introduction"
        chunk = f"=== {title} ===\n{text}\n\n"
        segments.append(
            {"title": title, "start_s": None, "pages": None, "offset": offset}
        )
        chunks.append(chunk)
        offset += len(chunk)
    full_text = "".join(chunks)
    words = len(full_text.split())
    metadata = {
        "source_type": "article",
        "title": page.og_title or page.title or "Untitled article",
        "author": (
            page.author or page.ld_author or page.twitter_creator
            or page.rel_author
        ),
        "date": page.date or page.ld_date or page.time_date,
        "origin": source,
        "language": page.language,
        "words": words,
        "est_tokens": utils.estimate_tokens(words),
        "segments": segments,
    }
    return full_text, metadata
