"""Tests for Hacker News / Reddit threads. No network: _fetch_json and
urllib are mocked."""
import email.message
import io
import json
import urllib.error

import pytest

import extract
from extractor import config, utils
from extractor.parsers import thread
from extractor.utils import ExtractError

HN_URL = "https://news.ycombinator.com/item?id=4242"
HN_ITEM = {
    "id": 4242,
    "type": "story",
    "author": "founder",
    "title": "Show HN: A tiny database",
    "url": "https://tinydb.example.com/",
    "text": None,
    "points": 321,
    "created_at": "2026-09-30T12:00:00.000Z",
    "children": [
        {
            "id": 1, "type": "comment", "author": "alice", "points": None,
            "text": (
                "<p>Great &amp; useful &#x2F; fast.<p>We cut p99 from 80 ms "
                'to 12 ms. See <a href="https://bench.example.com/very/long/path"'
                ' rel="nofollow">https://bench.example.com/very/lo...</a>'
            ),
            "children": [
                {
                    "id": 2, "type": "comment", "author": "bob",
                    "text": "Did you test <i>writes</i>?",
                    "children": [
                        {"id": 3, "type": "comment", "author": "alice",
                         "text": "Yes, 40k/s.", "children": []},
                    ],
                },
            ],
        },
        # Deleted comment: no author, no text - skipped, replies kept.
        {
            "id": 4, "type": "comment", "author": None, "text": None,
            "children": [
                {"id": 5, "type": "comment", "author": "carol",
                 "text": "Orphan reply survives.", "children": []},
            ],
        },
        {
            "id": 6, "type": "comment", "author": "dave",
            "text": "<pre><code>  indented code\n  line two</code></pre>",
            "children": [],
        },
    ],
}


def _install_fetch(monkeypatch, payload, rank=None):
    calls = []

    def fake(url):
        calls.append(url)
        if "firebaseio" in url:
            if rank is None:
                raise ExtractError("rank API down")
            return {"kids": rank}
        return json.loads(json.dumps(payload))

    monkeypatch.setattr(thread, "_fetch_json", fake)
    return calls


def test_hn_thread_metadata(monkeypatch):
    calls = _install_fetch(monkeypatch, HN_ITEM)
    _, meta = thread.parse(HN_URL)
    assert calls == [
        "https://hn.algolia.com/api/v1/items/4242",
        "https://hacker-news.firebaseio.com/v0/item/4242.json",
    ]
    assert meta["source_type"] == "thread"
    assert meta["platform"] == "hackernews"
    assert meta["title"] == "Show HN: A tiny database"
    assert meta["origin"] == HN_URL
    assert meta["linked_url"] == "https://tinydb.example.com/"
    assert meta["author"] == "founder"
    assert meta["points"] == 321
    assert meta["date"] == "2026-09-30"
    assert meta["num_comments"] == 5
    assert meta["comments_extracted"] == 5
    assert meta["est_tokens"] == utils.estimate_tokens(meta["words"])


def test_hn_segments_are_post_then_top_level_subtrees(monkeypatch):
    _install_fetch(monkeypatch, HN_ITEM)
    full_text, meta = thread.parse(HN_URL)
    segs = meta["segments"]
    assert [s["url"] for s in segs] == [
        HN_URL,
        "https://news.ycombinator.com/item?id=1",
        "https://news.ycombinator.com/item?id=5",
        "https://news.ycombinator.com/item?id=6",
    ]
    assert segs[0]["title"] == "Show HN: A tiny database"
    assert segs[1]["title"].startswith("alice: Great & useful")
    for seg in segs:
        assert seg["start_s"] is None and seg["pages"] is None
        assert full_text[seg["offset"]:].startswith(f"=== {seg['title']} ===")
    assert "Link: https://tinydb.example.com/" in full_text[:segs[1]["offset"]]


def test_hn_top_level_comments_follow_site_rank(monkeypatch):
    # Deleted id 4 is ranked second; its reply (5) inherits that rank.
    _install_fetch(monkeypatch, HN_ITEM, rank=[6, 4, 1])
    _, meta = thread.parse(HN_URL)
    assert [s["url"].rsplit("=", 1)[1] for s in meta["segments"][1:]] == [
        "6", "5", "1",
    ]


def test_hn_comment_lines_have_author_depth_and_plain_text(monkeypatch):
    _install_fetch(monkeypatch, HN_ITEM)
    full_text, _ = thread.parse(HN_URL)
    assert "\nalice: Great & useful / fast.\nWe cut p99 from 80 ms to 12 ms." in full_text
    # Truncated anchor text is replaced by the full href.
    assert "https://bench.example.com/very/long/path" in full_text
    assert "\n  bob: Did you test writes?\n" in full_text
    assert "\n    alice: Yes, 40k/s.\n" in full_text
    # The deleted parent is skipped; its reply moves up a level.
    assert "\ncarol: Orphan reply survives.\n" in full_text
    assert "None" not in full_text
    assert "<" not in full_text
    assert "dave:\n  indented code\n  line two" in full_text


def test_hn_ask_post_text(monkeypatch):
    item = dict(HN_ITEM, url=None, title="Ask HN: How do you plan?",
                text="<p>Context here.<p>Second paragraph.", children=[])
    _install_fetch(monkeypatch, item)
    full_text, meta = thread.parse(HN_URL)
    assert meta["linked_url"] is None
    assert "Context here.\nSecond paragraph." in full_text
    assert len(meta["segments"]) == 1


def test_hn_comment_url_extracts_from_that_comment(monkeypatch):
    calls = _install_fetch(monkeypatch, dict(HN_ITEM, id=1, type="comment"))
    _, meta = thread.parse("https://news.ycombinator.com/item?id=1&p=2")
    assert calls == ["https://hn.algolia.com/api/v1/items/1"]
    assert meta["segments"][1]["url"] == "https://news.ycombinator.com/item?id=1"


# --- Reddit -----------------------------------------------------------------

REDDIT_URL = "https://www.reddit.com/r/python/comments/abc123/why_uv_wins/"


def _c(cid, author, body, score, replies=()):
    return {
        "kind": "t1",
        "data": {
            "id": cid, "author": author, "body": body, "score": score,
            "permalink": f"/r/python/comments/abc123/why_uv_wins/{cid}/",
            "replies": (
                {"kind": "Listing", "data": {"children": list(replies)}}
                if replies else ""
            ),
        },
    }


REDDIT_JSON = [
    {"kind": "Listing", "data": {"children": [{"kind": "t3", "data": {
        "id": "abc123", "title": "Why uv wins", "author": "op_user",
        "selftext": "Switched 40 repos &amp; saved hours.\n\nAMA.",
        "score": 812, "num_comments": 230, "subreddit": "python",
        "permalink": "/r/python/comments/abc123/why_uv_wins/",
        "url": "https://www.reddit.com/r/python/comments/abc123/why_uv_wins/",
        "is_self": True, "created_utc": 1767225600,
    }}]}},
    {"kind": "Listing", "data": {"children": [
        _c("c1", "low", "Meh.", 3),
        _c("c2", "top", "Lockfile is 10x faster.\n\nBenchmarks below.", 500, [
            _c("c3", "[deleted]", "[deleted]", 7),
            _c("c4", "replier", "Confirmed on CI.", 40),
        ]),
        _c("c5", "AutoModerator", "[removed]", 1),
        {"kind": "more", "data": {"count": 200, "children": ["x", "y"]}},
        _c("c6", "mid", "Pin your Python.", 90),
    ]}},
]


def test_reddit_thread_sorted_by_score_with_permalinks(monkeypatch):
    calls = _install_fetch(monkeypatch, REDDIT_JSON)
    full_text, meta = thread.parse(REDDIT_URL)
    assert calls == [
        "https://www.reddit.com/comments/abc123.json"
        "?sort=top&limit=500&raw_json=1"
    ]
    assert meta["platform"] == "reddit"
    assert meta["title"] == "Why uv wins"
    assert meta["origin"] == REDDIT_URL
    assert meta["subreddit"] == "python"
    assert meta["linked_url"] is None
    assert meta["author"] == "op_user"
    assert meta["points"] == 812
    assert meta["num_comments"] == 230
    assert meta["comments_extracted"] == 4
    assert meta["date"] == "2026-01-01"
    assert [s["url"] for s in meta["segments"][1:]] == [
        "https://www.reddit.com/r/python/comments/abc123/why_uv_wins/c2/",
        "https://www.reddit.com/r/python/comments/abc123/why_uv_wins/c6/",
        "https://www.reddit.com/r/python/comments/abc123/why_uv_wins/c1/",
    ]
    assert "\ntop (+500): Lockfile is 10x faster.\nBenchmarks below.\n" in full_text
    assert "\n  replier (+40): Confirmed on CI.\n" in full_text
    assert "[deleted]" not in full_text and "[removed]" not in full_text
    assert "Switched 40 repos & saved hours." in full_text


def test_reddit_link_post_and_url_variants(monkeypatch):
    data = json.loads(json.dumps(REDDIT_JSON))
    post = data[0]["data"]["children"][0]["data"]
    post.update(is_self=False, url="https://blog.example.com/uv", selftext="")
    for url in (
        "https://old.reddit.com/r/python/comments/abc123/why_uv_wins/",
        "https://np.reddit.com/r/python/comments/abc123/",
        "https://reddit.com/comments/abc123",
        "https://redd.it/abc123",
    ):
        calls = _install_fetch(monkeypatch, data)
        _, meta = thread.parse(url)
        assert calls[0].startswith("https://www.reddit.com/comments/abc123.json")
        assert meta["linked_url"] == "https://blog.example.com/uv"
        assert meta["origin"] == REDDIT_URL


def test_comment_cap_truncates_with_stderr_note(monkeypatch, capsys):
    monkeypatch.setattr(config, "THREAD_MAX_COMMENTS", 2)
    _install_fetch(monkeypatch, REDDIT_JSON)
    full_text, meta = thread.parse(REDDIT_URL)
    assert meta["comments_extracted"] == 2
    assert "Confirmed on CI." in full_text
    assert "Pin your Python." not in full_text
    assert "truncated" in capsys.readouterr().err


def test_byte_cap_truncates(monkeypatch, capsys):
    monkeypatch.setattr(config, "THREAD_MAX_BYTES", 30)
    _install_fetch(monkeypatch, REDDIT_JSON)
    _, meta = thread.parse(REDDIT_URL)
    assert meta["comments_extracted"] == 1
    assert "truncated" in capsys.readouterr().err


# --- fetching and errors ----------------------------------------------------


class _Response(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def test_fetch_json_sends_descriptive_user_agent(monkeypatch):
    seen = {}

    def fake_urlopen(request, timeout):
        seen["ua"] = request.get_header("User-agent")
        seen["timeout"] = timeout
        return _Response(b'{"ok": true}')

    monkeypatch.setattr(thread.urllib.request, "urlopen", fake_urlopen)
    assert thread._fetch_json("https://www.reddit.com/comments/x.json") == {"ok": True}
    assert seen["ua"].startswith("source-to-skill/")
    assert seen["timeout"] == config.FETCH_TIMEOUT_S


@pytest.mark.parametrize("code,needle", [(403, "blocked"), (429, "rate-limit")])
def test_reddit_http_errors_are_explained(monkeypatch, code, needle):
    def fake_urlopen(request, timeout):
        raise urllib.error.HTTPError(
            request.full_url, code, "nope", email.message.Message(), None
        )

    monkeypatch.setattr(thread.urllib.request, "urlopen", fake_urlopen)
    with pytest.raises(ExtractError, match=needle):
        thread.parse(REDDIT_URL)


def test_non_json_response_is_explained(monkeypatch):
    monkeypatch.setattr(
        thread.urllib.request, "urlopen",
        lambda request, timeout: _Response(b"<html>blocked</html>"),
    )
    with pytest.raises(ExtractError, match="not JSON"):
        thread.parse(REDDIT_URL)


def test_hn_missing_item(monkeypatch):
    def fake_urlopen(request, timeout):
        raise urllib.error.HTTPError(
            request.full_url, 404, "nope", email.message.Message(), None
        )

    monkeypatch.setattr(thread.urllib.request, "urlopen", fake_urlopen)
    with pytest.raises(ExtractError, match="HTTP 404"):
        thread.parse(HN_URL)


@pytest.mark.parametrize(
    "source",
    [
        HN_URL,
        "https://news.ycombinator.com/item?id=1&p=2",
        REDDIT_URL,
        "https://old.reddit.com/r/AskHistorians/comments/xyz9/title/",
        "https://np.reddit.com/r/x/comments/abc/",
        "https://redd.it/abc123",
    ],
)
def test_detect_thread(source):
    assert utils.detect_source(source) == "thread"
    # Still forceable as an article page.
    assert utils.detect_source(source, "article") == "article"


@pytest.mark.parametrize(
    "source",
    ["https://news.ycombinator.com/news", "https://www.reddit.com/r/python/"],
)
def test_listing_pages_are_not_threads(source):
    assert utils.detect_source(source) == "article"


def test_cli_writes_outputs(monkeypatch, tmp_path, capsys):
    _install_fetch(monkeypatch, HN_ITEM)
    work = tmp_path / "work"
    assert extract.main([HN_URL, "--work-dir", str(work)]) == 0
    meta = json.loads((work / "metadata.json").read_text())
    assert meta["source_type"] == "thread"
    manifest = json.loads((work / "source.json").read_text())
    assert manifest["segments"][1]["key"] == "https://news.ycombinator.com/item?id=1"
    assert json.loads(capsys.readouterr().out)["segments"] == 4


def test_reddit_comment_with_blank_body_is_skipped(monkeypatch):
    # "&nbsp;" unescapes to whitespace: no lines left, so the comment is
    # treated as deleted (replies promoted) instead of crashing _render.
    data = json.loads(json.dumps(REDDIT_JSON))
    data[1]["data"]["children"].insert(0, _c(
        "c9", "blank", "&nbsp;", 999, [_c("c10", "kid", "Still here.", 2)],
    ))
    _install_fetch(monkeypatch, data)
    full_text, meta = thread.parse(REDDIT_URL)
    assert "blank" not in full_text
    assert "kid (+2): Still here." in full_text
    assert meta["comments_extracted"] == 5


def test_truncated_flag_in_metadata(monkeypatch):
    _install_fetch(monkeypatch, REDDIT_JSON)
    assert thread.parse(REDDIT_URL)[1]["truncated"] is False
    monkeypatch.setattr(config, "THREAD_MAX_COMMENTS", 2)
    assert thread.parse(REDDIT_URL)[1]["truncated"] is True


def test_hn_rank_fallback_warns(monkeypatch, capsys):
    _install_fetch(monkeypatch, HN_ITEM)
    thread.parse(HN_URL)
    assert "WARNING" in capsys.readouterr().err


@pytest.mark.parametrize("payload", [None, [1, 2], "kids", {"kids": "x"}])
def test_hn_rank_tolerates_non_dict_json(monkeypatch, capsys, payload):
    monkeypatch.setattr(thread, "_fetch_json", lambda url: payload)
    assert thread._hn_rank(4242) == {}
    assert "WARNING" in capsys.readouterr().err
