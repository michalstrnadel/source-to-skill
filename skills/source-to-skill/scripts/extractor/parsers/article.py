"""Web article parser: stdlib urllib fetch + HTMLParser content extraction."""
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
DATE_METAS = (
    "article:published_time", "date", "publish-date", "publication-date",
    "dc.date",
)

# charset=<token> inside a Content-Type http-equiv content value.
CONTENT_CHARSET_RE = re.compile(
    r"charset\s*=\s*[\"']?([A-Za-z0-9][A-Za-z0-9._-]*)", re.IGNORECASE
)


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


class _PageText(HTMLParser):
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
        self._drop = 0
        self._article = 0
        self._main = 0
        self._capture = None
        self._captured = []

    def _emit(self, kind, payload):
        self.items.append((kind, payload, self._article > 0, self._main > 0))

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
        elif name in DATE_METAS:
            self.date = self.date or content

    def handle_starttag(self, tag, attrs):
        if tag in DROP_TAGS:
            self._drop += 1
            return
        if self._drop:
            return
        if self._capture is not None and tag in BLOCK_TAGS:
            # Unclosed <hN>/<title> recovery: browsers auto-close an open
            # heading when the next block element starts; without this the
            # rest of the page would be swallowed into the heading buffer.
            self._flush_capture()
        attrs = dict(attrs)
        if tag == "meta":
            self._handle_meta(attrs)
        elif tag == "html":
            self.language = self.language or attrs.get("lang") or None
        elif tag == "article":
            self._article += 1
        elif tag == "main":
            self._main += 1
        elif tag == "br":
            if self._capture:
                self._captured.append(" ")
            else:
                self._emit("text", "\n")
        elif tag in HEADING_TAGS and self._capture is None:
            self._capture, self._captured = tag, []
        elif tag == "title" and self.title is None and self._capture is None:
            self._capture, self._captured = "title", []

    def handle_endtag(self, tag):
        if tag in DROP_TAGS:
            if self._drop:
                self._drop -= 1
            return
        if self._drop:
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
        if self._drop:
            return
        if self._capture is not None:
            self._captured.append(data)
        elif data:
            self._emit("text", data)

    def close(self):
        super().close()
        if self._capture is not None:  # heading still open at EOF
            self._flush_capture()


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
        "author": page.author,
        "date": page.date,
        "origin": source,
        "language": page.language,
        "words": words,
        "est_tokens": utils.estimate_tokens(words),
        "segments": segments,
    }
    return full_text, metadata
