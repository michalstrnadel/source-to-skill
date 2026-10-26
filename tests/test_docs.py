"""Tests for the documentation-site (llms.txt) parser. No network: fetches are mocked."""
import email.message
import io
import urllib.error

import pytest

from extractor import config, utils
from extractor.parsers import docs
from extractor.utils import ExtractError

BASE = "https://docs.example.com"


def _words(n, prefix="w"):
    return " ".join(f"{prefix}{i}" for i in range(n))


def _install(monkeypatch, pages):
    """Serve `pages` (url -> text or (text, content type)); 404 otherwise.

    Returns the list of requested URLs, in order.
    """
    calls = []

    def fake_get(url):
        calls.append(url)
        if url not in pages:
            raise urllib.error.HTTPError(url, 404, "Not Found", None, None)
        body = pages[url]
        content_type = "text/markdown"
        if isinstance(body, tuple):
            body, content_type = body
        if isinstance(body, Exception):
            raise body
        return body.encode("utf-8"), "utf-8", content_type

    monkeypatch.setattr(docs, "_get", fake_get)
    return calls


LLMS_TXT = f"""# Example Docs

> Example is a library for building things. These docs cover setup and the API.

Example uses semantic versioning. Read the quickstart first.

## Docs

- [Quickstart](https://docs.example.com/quickstart.md): install and first run
- [Configuration](/config): every option
- [API reference](https://docs.example.com/api/)

## Optional

- [Changelog](https://docs.example.com/changelog.md): release history
"""


def test_parse_llms_txt_fetches_linked_pages_in_order(monkeypatch):
    calls = _install(monkeypatch, {
        f"{BASE}/llms.txt": LLMS_TXT,
        f"{BASE}/quickstart.md": f"# Quickstart\n\n{_words(30, 'qs')}\n",
        f"{BASE}/config.md": f"# Configuration\n\n{_words(30, 'cfg')}\n",
        f"{BASE}/api/index.html.md": f"# API\n\n{_words(30, 'api')}\n",
        f"{BASE}/changelog.md": f"# Changelog\n\n{_words(10, 'log')}\n",
    })
    full_text, meta = docs.parse(f"{BASE}/llms.txt")
    assert meta["source_type"] == "docs"
    assert meta["title"] == "Example Docs"
    assert meta["origin"] == f"{BASE}/llms.txt"
    assert meta["format"] == "llms.txt"
    assert meta["summary"].startswith("Example is a library")
    assert meta["words"] == len(full_text.split())
    assert meta["est_tokens"] > 0
    titles = [s["title"] for s in meta["segments"]]
    assert titles == [
        "Overview", "Quickstart", "Configuration", "API reference", "Changelog",
    ]
    urls = [s.get("url") for s in meta["segments"]]
    assert urls[1:] == [
        f"{BASE}/quickstart.md", f"{BASE}/config", f"{BASE}/api/",
        f"{BASE}/changelog.md",
    ]
    for seg in meta["segments"]:
        assert seg["start_s"] is None
        assert seg["pages"] is None
        assert full_text[seg["offset"]:].startswith(f"=== {seg['title']} ===")
    by_title = {s["title"]: s for s in meta["segments"]}
    assert by_title["Quickstart"]["section"] == "Docs"
    assert by_title["Quickstart"]["notes"] == "install and first run"
    assert by_title["Changelog"]["section"] == "Optional"
    assert by_title["Changelog"]["optional"] is True
    assert "optional" not in by_title["Quickstart"]
    assert "semantic versioning" in full_text
    assert "qs0" in full_text and "cfg0" in full_text and "api0" in full_text
    assert meta["sections"] == [
        {"title": "Docs", "links": 3, "optional": False},
        {"title": "Optional", "links": 1, "optional": True},
    ]
    # Sequential and in llms.txt order, the index first.
    assert calls[0] == f"{BASE}/llms.txt"
    assert calls.index(f"{BASE}/quickstart.md") < calls.index(f"{BASE}/config.md")


def test_html_link_falls_back_to_article_extraction(monkeypatch, capsys):
    html = (
        "<html><head><title>Config page</title></head><body>"
        "<nav>Home Menu</nav><main><h1>Configuration</h1>"
        f"<p>{_words(40, 'html')}</p></main></body></html>"
    )
    _install(monkeypatch, {
        f"{BASE}/llms.txt": "# Docs\n\n## Docs\n\n- [Config](https://docs.example.com/config)\n",
        f"{BASE}/config": (html, "text/html; charset=utf-8"),
    })
    full_text, meta = docs.parse(f"{BASE}/llms.txt")
    assert [s["title"] for s in meta["segments"]] == ["Config"]
    assert "html0" in full_text
    assert "Home Menu" not in full_text
    assert "<p>" not in full_text


def test_md_probe_returning_html_is_not_taken_as_markdown(monkeypatch):
    # SPAs answer every path with their HTML shell; that is not Markdown.
    shell = "<!doctype html><html><body><div id=root></div></body></html>"
    page = f"<html><body><article><p>{_words(40, 'real')}</p></article></body></html>"
    _install(monkeypatch, {
        f"{BASE}/llms.txt": "# Docs\n\n## Docs\n\n- [Guide](https://docs.example.com/guide)\n",
        f"{BASE}/guide.md": (shell, "text/html"),
        f"{BASE}/guide": (page, "text/html"),
    })
    full_text, _ = docs.parse(f"{BASE}/llms.txt")
    assert "real0" in full_text


def test_failed_pages_are_skipped_with_a_warning(monkeypatch, capsys):
    _install(monkeypatch, {
        f"{BASE}/llms.txt": (
            "# Docs\n\n## Docs\n\n"
            "- [Good](https://docs.example.com/good.md)\n"
            "- [Gone](https://docs.example.com/gone.md)\n"
        ),
        f"{BASE}/good.md": f"# Good\n\n{_words(20)}\n",
    })
    _, meta = docs.parse(f"{BASE}/llms.txt")
    assert [s["title"] for s in meta["segments"]] == ["Good"]
    assert meta["skipped"] == [
        {"title": "Gone", "url": f"{BASE}/gone.md", "reason": "HTTP 404"}
    ]
    assert "Gone" in capsys.readouterr().err


def test_fails_when_no_linked_page_is_usable(monkeypatch):
    _install(monkeypatch, {
        f"{BASE}/llms.txt": "# Docs\n\n## Docs\n\n- [Gone](https://docs.example.com/gone.md)\n",
    })
    with pytest.raises(ExtractError, match="none of the 1 linked page"):
        docs.parse(f"{BASE}/llms.txt")


def test_duplicate_links_and_fragments_fetch_once(monkeypatch):
    calls = _install(monkeypatch, {
        f"{BASE}/llms.txt": (
            "# Docs\n\n## Docs\n\n"
            "- [Intro](https://docs.example.com/intro.md)\n"
            "- [Intro, setup](https://docs.example.com/intro.md#setup)\n"
        ),
        f"{BASE}/intro.md": f"# Intro\n\n{_words(20)}\n",
    })
    _, meta = docs.parse(f"{BASE}/llms.txt")
    assert [s["title"] for s in meta["segments"]] == ["Intro"]
    assert calls.count(f"{BASE}/intro.md") == 1


def test_page_count_cap_drops_the_rest_with_a_warning(monkeypatch, capsys):
    monkeypatch.setattr(config, "DOCS_MAX_PAGES", 2)
    links = "\n".join(
        f"- [P{i}](https://docs.example.com/p{i}.md)" for i in range(4)
    )
    pages = {f"{BASE}/llms.txt": f"# Docs\n\n## Docs\n\n{links}\n"}
    pages.update({f"{BASE}/p{i}.md": f"text {i} {_words(5)}" for i in range(4)})
    calls = _install(monkeypatch, pages)
    _, meta = docs.parse(f"{BASE}/llms.txt")
    assert [s["title"] for s in meta["segments"]] == ["P0", "P1"]
    assert f"{BASE}/p2.md" not in calls
    assert "page cap" in capsys.readouterr().err
    assert meta["dropped"] == [
        {"title": f"P{i}", "url": f"{BASE}/p{i}.md", "reason": "over page cap"}
        for i in (2, 3)
    ]


def test_text_cap_drops_later_pages(monkeypatch, capsys):
    monkeypatch.setattr(config, "DOCS_TEXT_CAP_BYTES", 300)
    _install(monkeypatch, {
        f"{BASE}/llms.txt": (
            "# Docs\n\n## Docs\n\n"
            "- [Big](https://docs.example.com/big.md)\n"
            "- [More](https://docs.example.com/more.md)\n"
        ),
        f"{BASE}/big.md": "x " * 100,
        f"{BASE}/more.md": "y " * 100,
    })
    _, meta = docs.parse(f"{BASE}/llms.txt")
    assert [s["title"] for s in meta["segments"]] == ["Big"]
    assert "text cap" in capsys.readouterr().err
    assert meta["dropped"] == [{
        "title": "More", "url": f"{BASE}/more.md", "reason": "over text cap",
    }]


def test_optional_section_skipped_when_docs_are_large(monkeypatch, capsys):
    monkeypatch.setattr(config, "DOCS_OPTIONAL_BUDGET_BYTES", 100)
    calls = _install(monkeypatch, {
        f"{BASE}/llms.txt": (
            "# Docs\n\n## Docs\n\n- [Main](https://docs.example.com/main.md)\n\n"
            "## Optional\n\n- [Extra](https://docs.example.com/extra.md)\n"
        ),
        f"{BASE}/main.md": "m " * 200,
        f"{BASE}/extra.md": "e " * 10,
    })
    _, meta = docs.parse(f"{BASE}/llms.txt")
    assert [s["title"] for s in meta["segments"]] == ["Main"]
    assert f"{BASE}/extra.md" not in calls
    assert meta["optional_skipped"] == 1
    assert "Optional" in capsys.readouterr().err


def test_parse_llms_txt_rejects_html(monkeypatch):
    _install(monkeypatch, {
        f"{BASE}/llms.txt": ("<!DOCTYPE html><html><body>Not found</body></html>", "text/html"),
    })
    with pytest.raises(ExtractError, match="llms"):
        docs.parse(f"{BASE}/llms.txt")


LLMS_FULL = f"""# Getting started
Source: https://docs.example.com/getting-started

{_words(30, 'gs')}

```bash
# install it - a shell comment, not a heading
pip install example
```

# Configuration
Source: https://docs.example.com/configuration

{_words(30, 'cfg')}

## Options

{_words(10, 'opt')}

# API
{_words(30, 'api')}
"""


def test_parse_llms_full_splits_on_h1_and_respects_fences(monkeypatch):
    _install(monkeypatch, {f"{BASE}/llms-full.txt": LLMS_FULL})
    full_text, meta = docs.parse(f"{BASE}/llms-full.txt")
    assert meta["source_type"] == "docs"
    assert meta["format"] == "llms-full.txt"
    assert meta["origin"] == f"{BASE}/llms-full.txt"
    titles = [s["title"] for s in meta["segments"]]
    assert titles == ["Getting started", "Configuration", "API"]
    assert meta["segments"][0]["url"] == f"{BASE}/getting-started"
    assert meta["segments"][1]["url"] == f"{BASE}/configuration"
    assert "url" not in meta["segments"][2]
    assert "pip install example" in full_text
    assert "opt0" in full_text  # H2 stays inside its H1 segment
    for seg in meta["segments"]:
        assert full_text[seg["offset"]:].startswith(f"=== {seg['title']} ===")
    assert meta["words"] == len(full_text.split())


def test_parse_llms_full_with_one_h1_splits_on_h2(monkeypatch):
    text = (
        "# Example Docs\n\n> The summary.\n\n"
        f"## Install\n{_words(20, 'a')}\n\n## Use\n{_words(20, 'b')}\n"
    )
    _install(monkeypatch, {f"{BASE}/llms-full.txt": text})
    full_text, meta = docs.parse(f"{BASE}/llms-full.txt")
    assert meta["title"] == "Example Docs"
    assert [s["title"] for s in meta["segments"]] == [
        "Introduction", "Install", "Use",
    ]
    assert "The summary." in full_text


def test_parse_llms_full_without_headings_is_one_segment(monkeypatch):
    _install(monkeypatch, {f"{BASE}/llms-full.txt": _words(50)})
    _, meta = docs.parse(f"{BASE}/llms-full.txt")
    assert [s["title"] for s in meta["segments"]] == ["Full text"]
    assert meta["title"] == "docs.example.com"


def test_forced_url_prefers_llms_full_under_the_path(monkeypatch):
    calls = _install(monkeypatch, {
        f"{BASE}/guide/llms-full.txt": LLMS_FULL,
        f"{BASE}/llms.txt": LLMS_TXT,
    })
    _, meta = docs.parse(f"{BASE}/guide/")
    assert meta["origin"] == f"{BASE}/guide/llms-full.txt"
    assert calls[0] == f"{BASE}/guide/llms-full.txt"


def test_forced_url_falls_back_to_origin_llms_txt(monkeypatch):
    calls = _install(monkeypatch, {
        f"{BASE}/llms.txt": "# Docs\n\n## Docs\n\n- [A](https://docs.example.com/a.md)\n",
        f"{BASE}/a.md": f"# A\n\n{_words(20)}",
    })
    _, meta = docs.parse(f"{BASE}/guide/install?x=1")
    assert meta["origin"] == f"{BASE}/llms.txt"
    assert calls[:4] == [
        f"{BASE}/guide/install/llms-full.txt",
        f"{BASE}/guide/install/llms.txt",
        f"{BASE}/guide/llms-full.txt",
        f"{BASE}/guide/llms.txt",
    ]


def test_forced_url_without_llms_files_fails_with_hint(monkeypatch):
    _install(monkeypatch, {})
    with pytest.raises(ExtractError, match="No llms.txt") as err:
        docs.parse(f"{BASE}/guide")
    assert "--type article" in str(err.value)


def test_forced_url_skips_html_fallback_pages(monkeypatch):
    # A site answering every path with its HTML shell has no llms.txt.
    shell = ("<!doctype html><html><body>app</body></html>", "text/html")
    _install(monkeypatch, {
        f"{BASE}/llms-full.txt": shell,
        f"{BASE}/llms.txt": shell,
    })
    with pytest.raises(ExtractError, match="No llms.txt"):
        docs.parse(BASE)


def test_get_sends_user_agent_timeout_and_caps_size(monkeypatch):
    seen = {}

    class FakeResponse(io.BytesIO):
        def __init__(self, data):
            super().__init__(data)
            self.headers = email.message.Message()
            self.headers["Content-Type"] = "text/plain; charset=utf-8"

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    def fake_urlopen(request, timeout):
        seen["ua"] = request.get_header("User-agent")
        seen["timeout"] = timeout
        return FakeResponse(b"a" * 50)

    monkeypatch.setattr(docs.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(config, "DOCS_TEXT_CAP_BYTES", 10)
    raw, charset, content_type = docs._get(f"{BASE}/llms.txt")
    assert len(raw) == 11  # cap + 1, so callers can tell it was truncated
    assert charset == "utf-8"
    assert content_type == "text/plain"
    assert "Mozilla" in seen["ua"]
    assert seen["timeout"] == config.FETCH_TIMEOUT_S


def test_page_over_the_size_cap_is_skipped_not_cut(monkeypatch, capsys):
    monkeypatch.setattr(config, "DOCS_TEXT_CAP_BYTES", 300)
    # _get reads at most cap + 1 bytes; a page that fills them is cut.
    calls = _install(monkeypatch, {
        f"{BASE}/llms.txt": (
            "# Docs\n\n## Docs\n\n"
            "- [Huge](https://docs.example.com/huge.md)\n"
            "- [Small](https://docs.example.com/small.md)\n"
        ),
        f"{BASE}/huge.md": "é" * 151,
        f"{BASE}/small.md": "small page",
    })
    full_text, meta = docs.parse(f"{BASE}/llms.txt")
    assert [s["title"] for s in meta["segments"]] == ["Small"]
    assert "é" not in full_text
    assert meta["skipped"] == [{
        "title": "Huge", "url": f"{BASE}/huge.md", "reason": "over size cap",
    }]
    assert f"{BASE}/huge" not in calls  # no HTML retry of a too-big page
    assert "Huge" in capsys.readouterr().err


def test_no_dropped_pages_is_an_empty_list(monkeypatch):
    _install(monkeypatch, {f"{BASE}/llms-full.txt": LLMS_FULL})
    assert docs.parse(f"{BASE}/llms-full.txt")[1]["dropped"] == []


def test_llms_full_over_the_cap_records_dropped(monkeypatch):
    monkeypatch.setattr(config, "DOCS_TEXT_CAP_BYTES", 100)
    _install(monkeypatch, {f"{BASE}/llms-full.txt": LLMS_FULL})
    meta = docs.parse(f"{BASE}/llms-full.txt")[1]
    assert meta["dropped"] == [{
        "title": "llms-full.txt", "url": f"{BASE}/llms-full.txt",
        "reason": "over text cap",
    }]


def test_llms_full_repeated_titles_get_unique_keys(monkeypatch):
    text = (
        f"# Setup\n{_words(20, 'a')}\n\n# Setup\n{_words(20, 'b')}\n\n"
        f"# Use\nSource: {BASE}/use\n{_words(20, 'c')}\n"
    )
    _install(monkeypatch, {f"{BASE}/llms-full.txt": text})
    meta = docs.parse(f"{BASE}/llms-full.txt")[1]
    keys = [utils.segment_key(s) for s in meta["segments"]]
    assert keys == ["Setup", "Setup (2)", f"{BASE}/use"]
