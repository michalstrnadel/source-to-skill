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


def test_nested_block_inside_inline_text_starts_a_new_line():
    page = article._PageText()
    page.feed(
        "<article><ul><li><strong>Sectioning</strong>:<ul>"
        "<li>Implementing guardrails</li></ul></li></ul></article>"
    )
    page.close()
    text = "".join(item[1] for item in page.items)
    assert "Sectioning:\nImplementing guardrails" in text


def test_time_element_is_date_fallback():
    page = article._PageText()
    page.feed('<p>Written on <time datetime="2018-06-27">June 27</time></p>')
    page.close()
    assert page.date is None
    assert page.time_date == "2018-06-27"


def _page_text(html):
    page = article._PageText()
    page.feed(html)
    page.close()
    return article._clean(item[1] for item in page.items)


def test_table_renders_as_pipe_rows_with_header_separator():
    text = _page_text(
        "<article><p>Before</p><table>"
        "<thead><tr><th>Model</th><th>BLEU\n score</th></tr></thead>"
        "<tbody><tr><td><p>Base</p><p>model</p></td><td>27.3</td></tr>"
        "<tr><td>Big</td><td>28.4</td></tr></tbody>"
        "</table><p>After</p></article>"
    )
    assert text.splitlines() == [
        "Before",
        "| Model | BLEU score |",
        "| --- | --- |",
        "| Base model | 27.3 |",
        "| Big | 28.4 |",
        "After",
    ]


def test_table_without_header_has_no_separator_and_escapes_pipes():
    text = _page_text(
        "<table><tr><td>a|b</td><td>c<br>d</td></tr>"
        "<tr><td>e</td><td></td></tr></table>"
    )
    assert text.splitlines() == ["| a\\|b | c d |", "| e |  |"]


def test_nested_table_is_flattened_into_its_cell():
    text = _page_text(
        "<table><tr><th>Outer</th><th>Detail</th></tr>"
        "<tr><td>x</td><td><table><tr><td>in1</td><td>in2</td></tr>"
        "<tr><td>in3</td></tr></table></td></tr></table>"
    )
    assert text.splitlines() == [
        "| Outer | Detail |",
        "| --- | --- |",
        "| x | in1 in2 in3 |",
    ]


def test_single_column_layout_table_keeps_plain_lines():
    text = _page_text(
        "<table><tr><td><p>First paragraph.</p><p>Second one.</p></td></tr>"
        "</table>"
    )
    assert text.splitlines() == ["First paragraph.", "Second one."]


def test_layout_table_with_only_one_non_empty_cell_per_row_is_plain_text():
    # Illustrated Transformer: a banner table with an alt-less image cell.
    text = _page_text(
        '<table><tr><td><a href="/b"><img src="b.png" width="200"></a></td>'
        "<td><b>Update:</b> This post is now a book!</td></tr></table>"
    )
    assert text.splitlines() == ["Update: This post is now a book!"]


def test_heading_inside_table_cell_is_cell_text_not_segment():
    page = article._PageText()
    page.feed("<table><tr><td><h2>Cell head</h2></td><td>v</td></tr></table>")
    page.close()
    assert all(kind == "text" for kind, *_ in page.items)
    assert "| Cell head | v |" in "".join(i[1] for i in page.items)


def test_unclosed_table_is_flushed_at_eof():
    text = _page_text("<table><tr><td>a</td><td>b")
    assert text == "| a | b |"


def test_images_with_alt_become_markers_and_figcaptions_are_tagged():
    text = _page_text(
        "<article><p>Intro</p><figure>"
        '<img src="x.png" alt="Encoder  stack diagram">'
        "<figcaption> The <em>encoder</em> stack</figcaption></figure>"
        '<img src="deco.png" alt="">'
        '<img src="pixel.gif" alt="tracker" width="1" height="1">'
        '<img src="noalt.png"></article>'
    )
    assert text.splitlines() == [
        "Intro",
        "[image: Encoder stack diagram]",
        "[figure] The encoder stack",
    ]


def test_bold_label_without_space_gets_one():
    text = _page_text(
        "<p><strong>Label:</strong>Text here</p>"
        "<p><b>Hel</b>lo world</p>"
        "<p><b>Ratio:</b>3 and <b>Spaced:</b> fine</p>"
    )
    assert text.splitlines() == [
        "Label: Text here", "Hello world", "Ratio:3 and Spaced: fine",
    ]


def _meta_for(monkeypatch, head="", body_extra=""):
    page = _page(
        head="<title>T</title>" + head,
        body=f"{body_extra}<article>{LONG_PARAGRAPH}</article>",
    )
    _install_fetch(monkeypatch, page)
    return article.parse(URL)[1]


def test_author_and_date_from_json_ld(monkeypatch):
    meta = _meta_for(
        monkeypatch,
        head='<script type="application/ld+json">'
        '{"@context": "https://schema.org", "@graph": ['
        '{"@type": "WebSite", "name": "Site"},'
        '{"@type": "Article", "author": [{"@type": "Person", "name": "Ada"},'
        ' {"@id": "#bob"}], "datePublished": "2024-12-19"},'
        '{"@type": "Person", "@id": "#bob", "name": "Bob"}]}</script>',
    )
    assert meta["author"] == "Ada, Bob"
    assert meta["date"] == "2024-12-19"


def test_json_ld_string_author_and_list_root(monkeypatch):
    meta = _meta_for(
        monkeypatch,
        head='<script type="application/ld+json">'
        '[{"@type": "BlogPosting", "author": "Solo Writer"}]</script>',
    )
    assert meta["author"] == "Solo Writer"


def test_broken_json_ld_never_raises(monkeypatch):
    meta = _meta_for(
        monkeypatch,
        head='<script type="application/ld+json">{not json</script>'
        '<script type="application/ld+json">{"author": 42}</script>'
        '<script type="application/ld+json">"just a string"</script>',
    )
    assert meta["author"] is None
    assert meta["date"] is None


def test_regular_scripts_still_dropped(monkeypatch):
    page = _page(
        head="<title>T</title>",
        body='<article><script>{"author": {"name": "Nope"}}</script>'
        f"{LONG_PARAGRAPH}</article>",
    )
    _install_fetch(monkeypatch, page)
    full_text, meta = article.parse(URL)
    assert "Nope" not in full_text
    assert meta["author"] is None


def test_meta_author_beats_json_ld(monkeypatch):
    meta = _meta_for(
        monkeypatch,
        head='<meta name="author" content="Meta Name">'
        '<script type="application/ld+json">'
        '{"author": {"name": "LD Name"}}</script>',
    )
    assert meta["author"] == "Meta Name"


def test_author_from_twitter_creator(monkeypatch):
    meta = _meta_for(
        monkeypatch, head='<meta name="twitter:creator" content="@jay">'
    )
    assert meta["author"] == "@jay"


def test_author_from_rel_author_link_even_in_header(monkeypatch):
    meta = _meta_for(
        monkeypatch,
        body_extra='<header>By <a rel="author" href="/u/k">Kim  Lee</a>'
        "</header>",
    )
    assert meta["author"] == "Kim Lee"
