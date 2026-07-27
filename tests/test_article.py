"""Tests for the web article parser. No network: urllib is mocked."""
import email.message
import urllib.error

import pytest

from extractor.parsers import article
from extractor.utils import ExtractError

URL = "https://example.com/blog/deep-focus"


def _words(n, prefix="w"):
    return " ".join(f"{prefix}{i}" for i in range(n))


def _page(head="", body=""):
    return f"<html><head>{head}</head><body>{body}</body></html>"


LONG_PARAGRAPH = f"<p>{_words(120, 'body')}</p>"

ARTICLE_PAGE = f"""<!DOCTYPE html>
<html lang="en">
<head>
<title>Deep Focus at Work</title>
<meta name="author" content="Jane Q. Writer">
<meta property="article:published_time" content="2026-05-04">
</head>
<body>
<nav><a href="/">Home</a> <a href="/tags">Tags</a></nav>
<article>
<header>Share buttons and byline chrome</header>
<p>Cats &amp; dogs &mdash; the intro. {_words(40, "intro")}</p>
<h2>Why It Matters</h2>
<p>{_words(40, "one")}</p>
<h2>What To Do</h2>
<p>{_words(40, "two")}</p>
</article>
<div>Popular posts sidebar</div>
<footer>All rights reserved boilerplate</footer>
</body>
</html>
"""


def _install_fetch(monkeypatch, page, charset=None):
    raw = page.encode("utf-8") if isinstance(page, str) else page
    monkeypatch.setattr(article, "_fetch", lambda url: (raw, charset))


def test_parse_article_page_builds_metadata_and_segments(monkeypatch):
    _install_fetch(monkeypatch, ARTICLE_PAGE)
    full_text, meta = article.parse(URL)
    assert meta["source_type"] == "article"
    assert meta["title"] == "Deep Focus at Work"
    assert meta["author"] == "Jane Q. Writer"
    assert meta["date"] == "2026-05-04"
    assert meta["language"] == "en"
    assert meta["origin"] == URL
    assert meta["words"] == len(full_text.split())
    titles = [s["title"] for s in meta["segments"]]
    assert titles == ["Introduction", "Why It Matters", "What To Do"]
    for seg in meta["segments"]:
        assert seg["start_s"] is None
        assert seg["pages"] is None
        assert full_text[seg["offset"]:].startswith(f"=== {seg['title']} ===")
    assert "intro0" in full_text
    assert "one0" in full_text
    assert "two0" in full_text


def test_parse_keeps_junk_out_of_article_scoped_text(monkeypatch):
    _install_fetch(monkeypatch, ARTICLE_PAGE)
    full_text, _ = article.parse(URL)
    assert "Home" not in full_text  # nav
    assert "Share buttons" not in full_text  # header inside <article>
    assert "Popular posts" not in full_text  # sibling div outside <article>
    assert "All rights reserved" not in full_text  # footer


def test_parse_decodes_html_entities(monkeypatch):
    _install_fetch(monkeypatch, ARTICLE_PAGE)
    full_text, _ = article.parse(URL)
    assert "Cats & dogs" in full_text
    assert "— the intro." in full_text


def test_parse_prefers_og_title(monkeypatch):
    page = _page(
        head='<title>Example Site | Blog</title>'
        '<meta property="og:title" content="The Real Title">',
        body=f"<article>{LONG_PARAGRAPH}</article>",
    )
    _install_fetch(monkeypatch, page)
    _, meta = article.parse(URL)
    assert meta["title"] == "The Real Title"


def test_parse_main_only_page(monkeypatch):
    page = _page(
        head="<title>Guide Site</title>",
        body="<div>Sidebar cruft outside main</div>"
        f"<main><h1>Setup Guide</h1>{LONG_PARAGRAPH}</main>",
    )
    _install_fetch(monkeypatch, page)
    full_text, meta = article.parse(URL)
    assert [s["title"] for s in meta["segments"]] == ["Setup Guide"]
    assert "body0" in full_text
    assert "Sidebar cruft" not in full_text


def test_parse_body_fallback_strips_junk_tags(monkeypatch):
    page = _page(
        head="<title>Plain Page</title>",
        body="<nav>Menu items</nav><header>Big banner</header>"
        f"{LONG_PARAGRAPH}"
        "<aside>Related posts</aside><form>Subscribe now</form>"
        "<script>var tracker = 1;</script><style>.a{color:red}</style>"
        "<noscript>Enable JS</noscript><svg><text>logo</text></svg>"
        "<footer>Legal footer</footer>",
    )
    _install_fetch(monkeypatch, page)
    full_text, meta = article.parse(URL)
    assert "body0" in full_text
    for junk in (
        "Menu items", "Big banner", "Related posts", "Subscribe now",
        "tracker", "color:red", "Enable JS", "logo", "Legal footer",
    ):
        assert junk not in full_text


def test_parse_page_without_headings_is_one_segment(monkeypatch):
    page = _page(head="<title>Flat</title>", body=LONG_PARAGRAPH)
    _install_fetch(monkeypatch, page)
    full_text, meta = article.parse(URL)
    assert meta["segments"] == [
        {"title": "Full text", "start_s": None, "pages": None, "offset": 0}
    ]
    assert full_text.startswith("=== Full text ===")


def test_parse_recovers_from_unclosed_heading(monkeypatch):
    # Browsers auto-close an open heading at the next block element; the
    # page text after the broken heading must not be swallowed.
    page = _page(
        head="<title>Broken</title>",
        body=f"<article><h2>Broken heading{LONG_PARAGRAPH}</article>",
    )
    _install_fetch(monkeypatch, page)
    full_text, meta = article.parse(URL)
    assert [s["title"] for s in meta["segments"]] == ["Broken heading"]
    assert "body0" in full_text


def test_parse_recovers_from_mismatched_heading_close(monkeypatch):
    # HTML5 recovery: any h1-h6 end tag closes the open heading.
    page = _page(
        head="<title>Broken</title>",
        body=f"<article><h2>Real Title</h3>{LONG_PARAGRAPH}</article>",
    )
    _install_fetch(monkeypatch, page)
    full_text, meta = article.parse(URL)
    assert [s["title"] for s in meta["segments"]] == ["Real Title"]
    assert "body0" in full_text


def test_parse_flushes_heading_still_open_at_eof(monkeypatch):
    page = (
        "<html><head><title>T</title></head>"
        f"<body>{LONG_PARAGRAPH}<h2>Trailing"
    )
    _install_fetch(monkeypatch, page)
    _, meta = article.parse(URL)
    assert [s["title"] for s in meta["segments"]] == [
        "Introduction", "Trailing",
    ]


def test_parse_drops_template_content(monkeypatch):
    page = _page(
        head="<title>T</title>",
        body="<article><template><p>hidden template junk</p></template>"
        f"{LONG_PARAGRAPH}</article>",
    )
    _install_fetch(monkeypatch, page)
    full_text, _ = article.parse(URL)
    assert "hidden template junk" not in full_text
    assert "body0" in full_text


def test_parse_too_short_page_fails_clearly(monkeypatch):
    page = _page(
        head="<title>Stub</title>",
        body="<article><p>Way too short to be an article.</p></article>",
    )
    _install_fetch(monkeypatch, page)
    with pytest.raises(ExtractError, match="readable article"):
        article.parse(URL)


def test_parse_uses_charset_from_meta(monkeypatch):
    page = _page(
        head='<meta charset="windows-1250"><title>Znaky</title>',
        body=f"<p>Příliš žluťoučký "
        f"kůň {_words(120, 'cz')}</p>",
    )
    _install_fetch(monkeypatch, page.encode("windows-1250"))
    full_text, _ = article.parse(URL)
    assert "žluťoučký kůň" in full_text


def test_parse_uses_charset_from_http_equiv_meta(monkeypatch):
    page = _page(
        head='<meta http-equiv="Content-Type" '
        'content="text/html; charset=windows-1250"><title>Znaky</title>',
        body=f"<p>Příliš žluťoučký kůň {_words(120, 'cz')}</p>",
    )
    _install_fetch(monkeypatch, page.encode("windows-1250"))
    full_text, _ = article.parse(URL)
    assert "žluťoučký kůň" in full_text


def test_parse_ignores_charset_inside_other_meta_attributes(monkeypatch):
    # "charset=" inside a meta description must not beat the real
    # <meta charset="utf-8"> declaration that follows it.
    page = _page(
        head='<meta name="description" '
        'content="migrating from charset=iso-8859-2 pages">'
        '<meta charset="utf-8"><title>Znaky</title>',
        body=f"<p>Příliš žluťoučký kůň {_words(120, 'cz')}</p>",
    )
    _install_fetch(monkeypatch, page)  # UTF-8 bytes, no header charset
    full_text, _ = article.parse(URL)
    assert "žluťoučký kůň" in full_text


def test_parse_uses_charset_from_header(monkeypatch):
    page = _page(
        head="<title>Cafe</title>",
        body=f"<p>café stories {_words(120, 'fr')}</p>",
    )
    _install_fetch(monkeypatch, page.encode("latin-1"), charset="latin-1")
    full_text, _ = article.parse(URL)
    assert "café stories" in full_text


class _FakeResponse:
    def __init__(self, raw):
        self._raw = raw
        self.headers = email.message.Message()

    def read(self):
        return self._raw

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def test_fetch_sends_browser_user_agent_and_timeout(monkeypatch):
    seen = {}

    def fake_urlopen(request, timeout=None):
        seen["ua"] = request.get_header("User-agent")
        seen["timeout"] = timeout
        return _FakeResponse(b"<html></html>")

    monkeypatch.setattr(article.urllib.request, "urlopen", fake_urlopen)
    raw, charset = article._fetch(URL)
    assert raw == b"<html></html>"
    assert charset is None
    assert seen["ua"].startswith("Mozilla/5.0")
    assert seen["timeout"] == article.config.FETCH_TIMEOUT_S


def test_parse_turns_http_error_into_extract_error(monkeypatch):
    def fake_urlopen(request, timeout=None):
        raise urllib.error.HTTPError(URL, 404, "Not Found", None, None)

    monkeypatch.setattr(article.urllib.request, "urlopen", fake_urlopen)
    with pytest.raises(ExtractError, match="HTTP 404"):
        article.parse(URL)


def test_parse_turns_network_error_into_extract_error(monkeypatch):
    def fake_urlopen(request, timeout=None):
        raise urllib.error.URLError("dns lookup failed")

    monkeypatch.setattr(article.urllib.request, "urlopen", fake_urlopen)
    with pytest.raises(ExtractError, match="Cannot fetch"):
        article.parse(URL)


def test_parse_turns_stalled_read_timeout_into_extract_error(monkeypatch):
    def fake_urlopen(request, timeout=None):
        raise TimeoutError("timed out")

    monkeypatch.setattr(article.urllib.request, "urlopen", fake_urlopen)
    with pytest.raises(ExtractError, match="Cannot fetch"):
        article.parse(URL)
