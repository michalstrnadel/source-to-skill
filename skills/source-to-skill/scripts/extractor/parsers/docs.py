"""Documentation-site parser: the llms.txt convention (llmstxt.org).

Two entry files exist. llms-full.txt is the whole documentation as one
Markdown file; it is split on its top-level headings. llms.txt is an index
(H1 title, blockquote summary, H2 sections of `- [name](url): notes`
links); every linked page is fetched - Markdown preferred, HTML reduced
to text with the article extractor - and becomes one segment.
"""
import re
import sys
import urllib.error
import urllib.request
from urllib.parse import urldefrag, urljoin, urlsplit, urlunsplit

from .. import config, utils
from ..utils import ExtractError
from . import article

LLMS_FILE_RE = re.compile(r"(?i)/llms(-full)?\.txt/?$")
FENCE_PREFIXES = ("```", "~~~")
HEADING_RE = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t]*#*[ \t]*$")
# `- [name](url)` or `- [name](url): notes` (also * and + bullets).
LINK_ITEM_RE = re.compile(
    r"^\s*[-*+]\s+\[(?P<name>[^\]]+)\]\((?P<url>[^)\s]+)"
    r"(?:\s+\"[^\"]*\")?\)\s*(?::\s*(?P<notes>.*))?$"
)
# Mintlify and others start each page in llms-full.txt with its URL.
SOURCE_LINE_RE = re.compile(r"^(?:Source|URL):\s*(https?://\S+)\s*$", re.I)
MARKDOWN_SUFFIXES = (".md", ".mdx", ".markdown", ".txt")
OPTIONAL_SECTION = "optional"


class _OverCap(Exception):
    """A page longer than DOCS_TEXT_CAP_BYTES: skipped, never cut."""


def _warn(message: str) -> None:
    print(f"WARNING: {message}", file=sys.stderr)


def _get(url: str):
    """Fetch `url`: (raw bytes, charset or None, media type).

    Reads at most DOCS_TEXT_CAP_BYTES + 1 bytes, so a caller can tell the
    body was cut. HTTP and network errors propagate to the caller.
    """
    request = urllib.request.Request(
        url, headers={"User-Agent": article.USER_AGENT}
    )
    with urllib.request.urlopen(
        request, timeout=config.FETCH_TIMEOUT_S
    ) as response:
        raw = response.read(config.DOCS_TEXT_CAP_BYTES + 1)
        headers = response.headers
        return raw, headers.get_content_charset(), headers.get_content_type()


def _reason(err: Exception) -> str:
    if isinstance(err, _OverCap):
        return "over size cap"
    if isinstance(err, urllib.error.HTTPError):
        return f"HTTP {err.code}"
    if isinstance(err, urllib.error.URLError):
        return f"network error: {err.reason}"
    return f"{type(err).__name__}: {err}"


def _looks_html(text: str, media_type: str) -> bool:
    if "html" in (media_type or ""):
        return True
    head = text.lstrip()[:200].lower()
    return head.startswith(("<!doctype html", "<html", "<head", "<body"))


def _fetch_text(url: str, whole: bool = False):
    """(text, is_html) for `url`; raises on HTTP/network errors.

    With `whole`, a body cut at DOCS_TEXT_CAP_BYTES raises _OverCap
    instead of returning a truncated (maybe mid-character) text.
    """
    raw, charset, media_type = _get(url)
    if whole and len(raw) > config.DOCS_TEXT_CAP_BYTES:
        raise _OverCap(url)
    text = article._decode(raw, charset)
    return text, _looks_html(text, media_type)


def _html_to_text(html: str) -> str:
    """Readable text of an HTML page via the article extractor."""
    page = article._PageText()
    page.feed(html)
    page.close()
    parts = []
    for title, text in article._sections(article._scoped_items(page.items)):
        if title:
            parts.append(f"## {title}")
        if text:
            parts.append(text)
    return "\n\n".join(parts).strip()


def _strip_query(url: str) -> str:
    scheme, netloc, path, _, _ = urlsplit(url)
    return urlunsplit((scheme, netloc, path, "", ""))


def _candidates(source: str) -> list[str]:
    """llms-full.txt then llms.txt URLs, deepest path prefix first."""
    scheme, netloc, path, _, _ = urlsplit(source)
    parts = [p for p in path.split("/") if p]
    if parts and "." in parts[-1]:
        parts.pop()  # a page (guide.html), not a folder
    prefixes = ["/" + "/".join(parts[:n]) for n in range(len(parts), 0, -1)]
    prefixes.append("")
    return [
        urlunsplit((scheme, netloc, f"{prefix}/{name}", "", ""))
        for prefix in prefixes
        for name in ("llms-full.txt", "llms.txt")
    ]


def _locate(source: str):
    """(url, text) of the first llms file that exists and is not HTML."""
    match = LLMS_FILE_RE.search(urlsplit(source).path)
    candidates = [source] if match else _candidates(source)
    for url in candidates:
        try:
            text, is_html = _fetch_text(url)
        except Exception as err:  # noqa: BLE001 - next candidate
            if match:
                raise ExtractError(
                    f"Cannot fetch {url} ({_reason(err)}).\n"
                    "Open it in a browser to check it exists; without an "
                    "llms.txt use --type article on a single page."
                ) from err
            continue
        if not is_html and text.strip():
            return url, text
        if match:
            raise ExtractError(
                f"{url} is not an llms.txt file (the server returned an "
                "HTML page).\n"
                "Check the URL in a browser; without an llms.txt use --type "
                "article on a single page."
            )
    raise ExtractError(
        f"No llms.txt or llms-full.txt found for {source}.\n"
        f"Tried: {', '.join(candidates)}.\n"
        "The site does not publish the llms.txt convention - extract single "
        "pages with --type article, or a GitHub repo of the docs as a repo."
    )


def _headings(lines):
    """[(line index, level, title)] for ATX headings outside code fences."""
    found = []
    fence = None
    for index, line in enumerate(lines):
        stripped = line.lstrip()
        if fence is not None:
            if stripped.startswith(fence):
                fence = None
            continue
        if stripped.startswith(FENCE_PREFIXES):
            fence = stripped[:3]
            continue
        match = HEADING_RE.match(line)
        if match:
            found.append((index, len(match.group(1)), match.group(2).strip()))
    return found


def _split_level(headings, total_chars: int):
    """Heading level to split llms-full.txt on: 1, 2, or None (no split)."""
    h1 = sum(1 for _, level, _ in headings if level == 1)
    h2 = sum(1 for _, level, _ in headings if level == 2)
    if h1 >= 2 and (
        total_chars / h1 <= config.DOCS_H1_SEGMENT_CHARS or h2 <= h1
    ):
        return 1
    if h2 >= 1:
        return 2
    if h1 >= 2:
        return 1
    return None


def _doc_title(headings):
    """The lone H1 when it opens the file: a title, not a boundary."""
    h1s = [(i, t) for i, lvl, t in headings if lvl == 1]
    if len(h1s) == 1 and headings[0][1] == 1:
        return h1s[0]
    return None


def _segments_from_full(text: str):
    """[(title, body, url or None)] split at the chosen heading level.

    Text before the first boundary becomes "Introduction" (dropped when
    empty); with no usable headings the file is one "Full text" segment.
    Sections left empty by the split (an H1 directly followed by an H2)
    are dropped.
    """
    lines = text.splitlines()
    headings = _headings(lines)
    level = _split_level(headings, len(text))
    if level is None:
        return [("Full text", text.strip(), None)]
    doc_title = _doc_title(headings) if level == 2 else None
    bounds = [
        (i, t) for i, lvl, t in headings
        if lvl <= level and (doc_title is None or i != doc_title[0])
    ]
    intro_start = doc_title[0] + 1 if doc_title else 0
    out = []
    intro = "\n".join(lines[intro_start:bounds[0][0]]).strip()
    if intro:
        out.append(("Introduction", intro, None))
    for n, (start, title) in enumerate(bounds):
        end = bounds[n + 1][0] if n + 1 < len(bounds) else len(lines)
        body_lines = lines[start + 1:end]
        url = None
        for k, line in enumerate(body_lines[:3]):
            source_line = SOURCE_LINE_RE.match(line.strip())
            if source_line:
                url = source_line.group(1)
                del body_lines[k]
                break
        body = "\n".join(body_lines).strip()
        if body:
            out.append((title, body, url))
    return out


def _parse_index(text: str, base_url: str) -> dict:
    """Spec structure of an llms.txt: title, summary, details, sections."""
    index = {"title": None, "summary": None, "details": [], "sections": []}
    quote = []
    section = None
    fence = None
    for line in text.splitlines():
        stripped = line.strip()
        if fence is not None:
            if stripped.startswith(fence):
                fence = None
            if section is None:
                index["details"].append(line)
            continue
        if stripped.startswith(FENCE_PREFIXES):
            fence = stripped[:3]
            if section is None:
                index["details"].append(line)
            continue
        heading = HEADING_RE.match(line)
        if heading and len(heading.group(1)) == 1 and index["title"] is None:
            index["title"] = heading.group(2).strip()
            continue
        if heading and len(heading.group(1)) == 2:
            section = {"title": heading.group(2).strip(), "links": []}
            index["sections"].append(section)
            continue
        if section is None:
            if stripped.startswith(">") and not index["details"]:
                quote.append(stripped.lstrip(">").strip())
            elif stripped or index["details"]:
                index["details"].append(line)
            continue
        link = LINK_ITEM_RE.match(line)
        if link:
            section["links"].append({
                "name": " ".join(link.group("name").split()),
                "url": urljoin(base_url, link.group("url")),
                "notes": (link.group("notes") or "").strip() or None,
            })
    index["summary"] = " ".join(q for q in quote if q) or None
    index["details"] = "\n".join(index["details"]).strip()
    return index


def _page_urls(url: str) -> list[str]:
    """URLs to try for a linked page: its Markdown twin first, per spec."""
    plain = urldefrag(url)[0]
    path = urlsplit(plain).path
    if path.lower().endswith(MARKDOWN_SUFFIXES):
        return [plain]
    stem = _strip_query(plain)
    md = stem + "index.html.md" if stem.endswith("/") else stem + ".md"
    return [md, plain]


def _fetch_page(url: str) -> str:
    """Page text, Markdown preferred; raises the last fetch error, or
    _OverCap at once for a page too big to keep whole."""
    last_err = None
    candidates = _page_urls(url)
    for n, candidate in enumerate(candidates):
        try:
            text, is_html = _fetch_text(candidate, whole=True)
        except _OverCap:
            raise
        except Exception as err:  # noqa: BLE001 - try the next form
            last_err = err
            continue
        if not is_html:
            return text.strip()
        if n + 1 < len(candidates):
            continue  # a .md probe answered with an HTML (SPA) shell
        return _html_to_text(text)
    raise last_err or ValueError("no content")


def _from_full(url: str, text: str):
    dropped = []
    if len(text.encode("utf-8")) > config.DOCS_TEXT_CAP_BYTES:
        _warn(
            f"{url} is over the text cap of {config.DOCS_TEXT_CAP_BYTES} "
            "bytes - the extracted docs are cut short. Extract its "
            "llms.txt index instead for page-by-page docs."
        )
        dropped.append({"title": "llms-full.txt", "url": url,
                        "reason": "over text cap"})
    parts = _segments_from_full(text)
    if not parts or not any(body for _, body, _ in parts):
        raise ExtractError(f"{url} is empty - nothing to extract.")
    # A single opening H1 names the docs; otherwise each H1 is a page.
    doc_title = _doc_title(_headings(text.splitlines()))
    meta = {
        "title": doc_title[1] if doc_title else urlsplit(url).netloc,
        "format": "llms-full.txt", "summary": None, "sections": [],
        "dropped": dropped,
    }
    entries = [
        {"title": t, "body": body, "url": seg_url, "extra": {}}
        for t, body, seg_url in parts
    ]
    return entries, meta, []


def _from_index(url: str, text: str):
    index = _parse_index(text, url)
    pages = []
    for section in index["sections"]:
        optional = section["title"].strip().lower() == OPTIONAL_SECTION
        for link in section["links"]:
            pages.append({**link, "section": section["title"],
                          "optional": optional})
    entries = []
    intro = "\n\n".join(
        part for part in (index["summary"], index["details"]) if part
    )
    if intro:
        entries.append(
            {"title": "Overview", "body": intro, "url": url, "extra": {}}
        )
    seen = set()
    unique = []
    for page in pages:
        key = urldefrag(page["url"])[0]
        if key not in seen:
            seen.add(key)
            unique.append({**page, "url": key})
    required = [p for p in unique if not p["optional"]]
    optional = [p for p in unique if p["optional"]]
    # Pages left out by the page or text cap: {title, url, reason}.
    dropped = []
    if len(required) > config.DOCS_MAX_PAGES:
        _warn(
            f"{url} links {len(required)} pages - page cap of "
            f"{config.DOCS_MAX_PAGES} reached, the rest are not fetched."
        )
        dropped += [
            {"title": p["name"], "url": p["url"], "reason": "over page cap"}
            for p in required[config.DOCS_MAX_PAGES:]
        ]
        required = required[:config.DOCS_MAX_PAGES]
    skipped = []
    total = sum(len(e["body"].encode("utf-8")) for e in entries)
    fetched = 0

    def fetch(page) -> bool:
        nonlocal total, fetched
        try:
            body = _fetch_page(page["url"])
        except Exception as err:  # noqa: BLE001 - skipped, never fatal
            reason = _reason(err)
            _warn(f"skipped {page['name']} ({page['url']}): {reason}")
            skipped.append(
                {"title": page["name"], "url": page["url"], "reason": reason}
            )
            return False
        if not body:
            _warn(f"skipped {page['name']} ({page['url']}): empty page")
            skipped.append({"title": page["name"], "url": page["url"],
                            "reason": "empty page"})
            return False
        size = len(body.encode("utf-8"))
        if fetched and total + size > config.DOCS_TEXT_CAP_BYTES:
            dropped.append({"title": page["name"], "url": page["url"],
                            "reason": "over text cap"})
            return False
        total += size
        fetched += 1
        extra = {"section": page["section"]}
        if page["notes"]:
            extra["notes"] = page["notes"]
        if page["optional"]:
            extra["optional"] = True
        entries.append({"title": page["name"], "body": body,
                        "url": page["url"], "extra": extra})
        return True

    for page in required:
        fetch(page)
    optional_skipped = 0
    budget = config.DOCS_OPTIONAL_BUDGET_BYTES
    for n, page in enumerate(optional):
        if total >= budget or fetched >= config.DOCS_MAX_PAGES:
            optional_skipped = len(optional) - n
            _warn(
                f"skipped {optional_skipped} page(s) of the Optional "
                f"section - the docs are already over {budget} bytes."
            )
            break
        fetch(page)
    over_text = [d["title"] for d in dropped if d["reason"] == "over text cap"]
    if over_text:
        _warn(
            f"{url}: text cap of {config.DOCS_TEXT_CAP_BYTES} bytes reached "
            f"- dropped {len(over_text)} page(s): {', '.join(over_text)}.\n"
            "The extracted docs are incomplete."
        )
    if unique and not fetched:
        raise ExtractError(
            f"{url}: none of the {len(unique)} linked page(s) could be "
            "fetched.\nCheck the links in a browser; if the site blocks "
            "scripts, try its llms-full.txt or a GitHub repo of the docs."
        )
    if not entries:
        raise ExtractError(
            f"{url} has no content and no page links - it is not a usable "
            "llms.txt index."
        )
    meta = {
        "title": index["title"] or urlsplit(url).netloc,
        "format": "llms.txt",
        "summary": index["summary"],
        "sections": [
            {
                "title": s["title"], "links": len(s["links"]),
                "optional": s["title"].strip().lower() == OPTIONAL_SECTION,
            }
            for s in index["sections"]
        ],
        "dropped": dropped,
    }
    if optional_skipped:
        meta["optional_skipped"] = optional_skipped
    return entries, meta, skipped


def parse(source: str):
    url, text = _locate(source)
    if LLMS_FILE_RE.search(urlsplit(url).path).group(1):
        entries, meta, skipped = _from_full(url, text)
    else:
        entries, meta, skipped = _from_index(url, text)
    chunks = []
    segments = []
    offset = 0
    keys = utils.unique_keys(entry["title"] for entry in entries)
    for entry, key in zip(entries, keys):
        chunk = f"=== {entry['title']} ===\n{entry['body']}\n\n"
        segment = {
            "title": entry["title"], "start_s": None, "pages": None,
            "offset": offset,
        }
        if entry["url"]:
            segment["url"] = entry["url"]
        else:
            # llms-full.txt sections without a Source: line repeat titles.
            segment["key"] = key
        segment.update(entry["extra"])
        segments.append(segment)
        chunks.append(chunk)
        offset += len(chunk)
    full_text = "".join(chunks)
    words = len(full_text.split())
    metadata = {
        "source_type": "docs",
        "title": meta["title"],
        "origin": url,
        "format": meta["format"],
        "summary": meta["summary"],
        "sections": meta["sections"],
        "page_count": len(segments),
        "dropped": meta["dropped"],
        "words": words,
        "est_tokens": utils.estimate_tokens(words),
        "segments": segments,
    }
    if "optional_skipped" in meta:
        metadata["optional_skipped"] = meta["optional_skipped"]
    if skipped:
        metadata["skipped"] = skipped
    return full_text, metadata
