"""Thread parser: Hacker News items and Reddit posts with their comments.

Hacker News comes from the public Algolia API (one request returns the
whole tree); Reddit from the post URL's `.json` view. The post is the
first segment; each top-level comment subtree is one more segment
(Reddit ordered by score, Hacker News in the site's rank order when the
official API answers, else Algolia's id order), keyed by the top
comment's permalink so refreshes diff cleanly. Deleted and removed
comments are skipped (their replies move up a level).
"""
import html
import json
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser

from .. import __version__, config, utils
from ..utils import ExtractError

HN_API = "https://hn.algolia.com/api/v1/items/{id}"
# The official API lists an item's replies (`kids`) in rank order; the
# Algolia tree is in id order. Used only to rank top-level comments.
HN_RANK_API = "https://hacker-news.firebaseio.com/v0/item/{id}.json"
HN_ITEM_URL = "https://news.ycombinator.com/item?id={id}"
REDDIT_API = (
    "https://www.reddit.com/comments/{id}.json?sort=top&limit=500&raw_json=1"
)
REDDIT_BASE = "https://www.reddit.com"
REMOVED_BODIES = {"[deleted]", "[removed]"}
TITLE_SNIPPET_CHARS = 60

# Marks a line inside <pre> whose indentation must survive cleanup.
PRE_LINE = "\x01"


def _fetch_json(url: str):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": config.THREAD_USER_AGENT.format(version=__version__),
            "Accept": "application/json",
        },
    )
    is_reddit = "reddit.com" in url
    try:
        with urllib.request.urlopen(
            request, timeout=config.FETCH_TIMEOUT_S
        ) as response:
            raw = response.read()
    except urllib.error.HTTPError as err:
        if err.code == 429:
            hint = (
                "The site is rate-limiting this machine - wait a few "
                "minutes and retry."
            )
        elif is_reddit and err.code in (401, 403):
            hint = (
                "Reddit blocked the unauthenticated request (\"blocked by "
                "network security\" - it refuses anonymous JSON access from "
                "many networks, VPNs and cloud IPs). Retry from another "
                "network (e.g. a home connection), or open the thread in a "
                "browser where you are signed in, print it to PDF and pass "
                "the file with --type book."
            )
        elif err.code == 404:
            hint = "The thread does not exist (or was deleted) - check the URL."
        else:
            hint = "Open the URL in a browser to check it, then retry."
        raise ExtractError(
            f"Cannot fetch thread: {url} returned HTTP {err.code}.\n{hint}"
        ) from err
    except (urllib.error.URLError, OSError) as err:
        raise ExtractError(
            f"Cannot fetch thread {url} ({err}).\n"
            "Check the URL and your network connection, then retry."
        ) from err
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as err:
        raise ExtractError(
            f"{url} returned a response that is not JSON (a login wall or "
            "block page?).\nOpen the URL in a browser to check it, retry "
            "later or from another network."
        ) from err


class _CommentHTML(HTMLParser):
    """Hacker News comment HTML -> text: <p> breaks, <pre> kept, links
    shown as their full href when HN truncated the anchor text."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self._pre = 0
        self._href = None
        self._anchor = []

    def handle_starttag(self, tag, attrs):
        if tag == "p":
            self.parts.append("\n")
        elif tag == "pre":
            self._pre += 1
            self.parts.append("\n" + PRE_LINE)
        elif tag == "a":
            self._href = dict(attrs).get("href")
            self._anchor = []
        elif tag == "br":
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag == "pre" and self._pre:
            self._pre -= 1
            self.parts.append("\n")
        elif tag == "a" and self._href is not None:
            text = "".join(self._anchor)
            if not text.strip() or (
                text.endswith("...") and self._href.startswith(text[:-3])
            ):
                text = self._href
            self.parts.append(text)
            self._href = None

    def handle_data(self, data):
        if self._href is not None:
            self._anchor.append(data)
        elif self._pre:
            self.parts.append(data.replace("\n", "\n" + PRE_LINE))
        else:
            self.parts.append(data)


def _lines(text: str) -> list:
    """Non-empty lines; whitespace collapsed except inside code blocks."""
    out = []
    for line in text.splitlines():
        if line.startswith(PRE_LINE):
            line = line[len(PRE_LINE):].rstrip()
        else:
            line = " ".join(line.split())
        if line.strip():
            out.append(line)
    return out


def _hn_text(raw) -> list:
    if not raw:
        return []
    parser = _CommentHTML()
    parser.feed(raw)
    parser.close()
    return _lines("".join(parser.parts))


def _plain_text(raw) -> list:
    """Reddit markdown bodies (raw_json=1): unescape, keep the lines."""
    return _lines(html.unescape(raw or ""))


def _promote(nodes) -> list:
    """Replace deleted nodes by their (promoted) replies."""
    out = []
    for node in nodes:
        if node["deleted"]:
            out.extend(_promote(node["children"]))
        else:
            out.append(node)
    return out


def _count(nodes) -> int:
    return sum(
        (0 if node["deleted"] else 1) + _count(node["children"])
        for node in nodes
    )


# --- Hacker News ------------------------------------------------------------


def _hn_rank(item_id) -> dict:
    """{comment id: rank} of an item's direct replies, {} if unavailable
    (with a stderr warning: the comments then keep Algolia's id order)."""
    try:
        item = _fetch_json(HN_RANK_API.format(id=item_id))
    except ExtractError as err:
        item, reason = None, str(err).splitlines()[0]
    else:
        reason = "unexpected response"
    kids = item.get("kids") if isinstance(item, dict) else None
    if isinstance(item, dict) and (kids is None or isinstance(kids, list)):
        return {kid: rank for rank, kid in enumerate(kids or [])}
    print(
        f"WARNING: Hacker News rank order unavailable ({reason}); top-level "
        "comments keep Algolia's id order.",
        file=sys.stderr,
    )
    return {}


def _hn_node(item) -> dict:
    lines = _hn_text(item.get("text"))
    return {
        "id": item.get("id"),
        "author": item.get("author"),
        "lines": lines,
        "score": None,
        "url": HN_ITEM_URL.format(id=item.get("id")),
        "deleted": not item.get("author") or not lines,
        "children": [
            _hn_node(child)
            for child in item.get("children") or []
            if child.get("type", "comment") == "comment"
        ],
    }


def _hackernews(item_id: str):
    item = _fetch_json(HN_API.format(id=item_id))
    created = item.get("created_at") or ""
    post = {
        "platform": "hackernews",
        "title": (
            item.get("title")
            or f"Hacker News item {item.get('id') or item_id}"
        ),
        "origin": HN_ITEM_URL.format(id=item.get("id") or item_id),
        "linked_url": item.get("url") or None,
        "author": item.get("author"),
        "points": item.get("points"),
        "date": created[:10] or None,
        "lines": _hn_text(item.get("text")),
    }
    if item.get("type") == "comment":
        # A comment permalink: the comment itself is the "post".
        post["lines"] = []
        comments = [_hn_node(item)]
    else:
        comments = _hn_node(item)["children"]
        rank = _hn_rank(item.get("id") or item_id)
        if rank:
            # Ranked replies first, in HN's order; the rest keep API order.
            comments.sort(key=lambda n: rank.get(n["id"], len(rank)))
    post["num_comments"] = _count(comments)
    return post, comments


# --- Reddit -----------------------------------------------------------------


def _reddit_node(child) -> dict:
    data = child.get("data") or {}
    body = (data.get("body") or "").strip()
    replies = data.get("replies")
    children = (
        replies.get("data", {}).get("children", [])
        if isinstance(replies, dict) else []
    )
    # A body that is only whitespace entities ("&nbsp;") has no lines.
    lines = _plain_text(body)
    return {
        "author": data.get("author"),
        "lines": lines,
        "score": data.get("score"),
        "url": REDDIT_BASE + (data.get("permalink") or ""),
        "deleted": (
            body in REMOVED_BODIES or not lines or not data.get("author")
        ),
        "children": [
            _reddit_node(c) for c in children if c.get("kind") == "t1"
        ],
    }


def _reddit(post_id: str):
    payload = _fetch_json(REDDIT_API.format(id=post_id))
    try:
        data = payload[0]["data"]["children"][0]["data"]
        listing = payload[1]["data"]["children"]
    except (KeyError, IndexError, TypeError) as err:
        raise ExtractError(
            f"Reddit returned an unexpected response for post {post_id}.\n"
            "Open the URL in a browser to check the post exists, then retry."
        ) from err
    selftext = (data.get("selftext") or "").strip()
    permalink = REDDIT_BASE + (data.get("permalink") or "")
    link = data.get("url") or ""
    created = data.get("created_utc")
    post = {
        "platform": "reddit",
        "subreddit": data.get("subreddit"),
        "title": data.get("title") or f"Reddit post {post_id}",
        "origin": permalink,
        "linked_url": (
            None if data.get("is_self") or not link
            or link.rstrip("/") == permalink.rstrip("/")
            else link
        ),
        "author": data.get("author"),
        "points": data.get("score"),
        "num_comments": data.get("num_comments"),
        "date": (
            datetime.fromtimestamp(created, timezone.utc).strftime("%Y-%m-%d")
            if isinstance(created, (int, float)) else None
        ),
        "lines": (
            [] if selftext in REMOVED_BODIES else _plain_text(selftext)
        ),
    }
    comments = [_reddit_node(c) for c in listing if c.get("kind") == "t1"]
    return post, comments


# --- rendering --------------------------------------------------------------


def _label(node) -> str:
    score = node["score"]
    return node["author"] + (f" ({score:+d})" if isinstance(score, int) else "")


def _render(node, depth, budget, out) -> bool:
    """Append a comment subtree's lines; False once the caps are hit."""
    if (
        budget["comments"] >= config.THREAD_MAX_COMMENTS
        or budget["bytes"] >= config.THREAD_MAX_BYTES
    ):
        budget["truncated"] = True
        return False
    indent = "  " * depth
    lines = node["lines"] or [""]
    if lines[0][:1].isspace():
        rendered = [f"{indent}{_label(node)}:"]
        rendered += [indent + line for line in lines]
    else:
        rendered = [f"{indent}{_label(node)}: {lines[0]}"]
        rendered += [indent + line for line in lines[1:]]
    out.extend(rendered)
    budget["comments"] += 1
    budget["bytes"] += sum(len(line.encode("utf-8")) + 1 for line in rendered)
    for child in _promote(node["children"]):
        if not _render(child, depth + 1, budget, out):
            return False
    return True


def _snippet(node) -> str:
    first = " ".join((node["lines"] or [""])[0].split())
    if len(first) > TITLE_SNIPPET_CHARS:
        first = first[:TITLE_SNIPPET_CHARS].rsplit(" ", 1)[0] + "..."
    return f"{node['author']}: {first}"


def _thread_id(source: str):
    for platform, pattern in (
        ("hackernews", config.HN_ITEM_PATTERN),
        ("reddit", config.REDDIT_POST_PATTERN),
        ("reddit", config.REDDIT_SHORT_PATTERN),
    ):
        match = re.match(pattern, source)
        if match:
            return platform, match.group("id")
    raise ExtractError(
        f"Unsupported thread URL: {source}\n"
        "Supported: Hacker News items (news.ycombinator.com/item?id=N) and "
        "Reddit posts (reddit.com/r/<sub>/comments/<id>/..., redd.it/<id>)."
    )


def parse(source: str):
    platform, thread_id = _thread_id(source)
    if platform == "hackernews":
        post, comments = _hackernews(thread_id)
    else:
        post, comments = _reddit(thread_id)
    roots = _promote(comments)
    if platform == "reddit":
        roots.sort(
            key=lambda n: n["score"] if isinstance(n["score"], int) else 0,
            reverse=True,
        )
    header = []
    if post["linked_url"]:
        header.append(f"Link: {post['linked_url']}")
    details = [
        f"r/{post['subreddit']}" if post.get("subreddit") else None,
        f"by {post['author']}" if post["author"] else None,
        f"{post['points']} points" if post["points"] is not None else None,
        (
            f"{post['num_comments']} comments"
            if post["num_comments"] is not None else None
        ),
        post["date"],
    ]
    header.append(" · ".join(d for d in details if d))
    body = "\n".join(header)
    if post["lines"]:
        body += "\n\n" + "\n".join(post["lines"])
    chunks = [f"=== {post['title']} ===\n{body}\n\n"]
    segments = [{
        "title": post["title"], "start_s": None, "pages": None,
        "offset": 0, "url": post["origin"],
    }]
    offset = len(chunks[0])
    budget = {"comments": 0, "bytes": 0, "truncated": False}
    for root in roots:
        lines = []
        complete = _render(root, 0, budget, lines)
        if lines:
            title = _snippet(root)
            chunk = f"=== {title} ===\n" + "\n".join(lines) + "\n\n"
            segments.append({
                "title": title, "start_s": None, "pages": None,
                "offset": offset, "url": root["url"],
            })
            chunks.append(chunk)
            offset += len(chunk)
        if not complete:
            break
    if budget["truncated"]:
        print(
            f"NOTE: thread truncated after {budget['comments']} comments "
            f"(caps: {config.THREAD_MAX_COMMENTS} comments, "
            f"{config.THREAD_MAX_BYTES:,} bytes); the lowest-ranked "
            "comments are left out.",
            file=sys.stderr,
        )
    full_text = "".join(chunks)
    words = len(full_text.split())
    metadata = {
        "source_type": "thread",
        "platform": platform,
        "title": post["title"],
        "origin": post["origin"],
        "linked_url": post["linked_url"],
        "author": post["author"],
        "points": post["points"],
        "date": post["date"],
        "num_comments": post["num_comments"],
        "comments_extracted": budget["comments"],
        "truncated": budget["truncated"],
        "words": words,
        "est_tokens": utils.estimate_tokens(words),
        "segments": segments,
    }
    if post.get("subreddit"):
        metadata["subreddit"] = post["subreddit"]
    return full_text, metadata
