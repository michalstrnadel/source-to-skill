import json

import pytest

from extractor import utils


def test_slugify_basic():
    assert utils.slugify("Attention Is All You Need!") == "attention-is-all-you-need"


def test_slugify_truncates_and_never_empty():
    assert len(utils.slugify("x" * 200)) <= 60
    assert utils.slugify("???") == "untitled"


@pytest.mark.parametrize(
    "source,expected",
    [
        ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "youtube"),
        ("https://youtu.be/dQw4w9WgXcQ", "youtube"),
        ("https://www.youtube.com/shorts/abc123", "youtube"),
        ("https://m.youtube.com/watch?v=dQw4w9WgXcQ", "youtube"),
        ("https://music.youtube.com/watch?v=dQw4w9WgXcQ", "youtube"),
        ("https://www.youtube.com/live/abc123", "youtube"),
        ("https://arxiv.org/abs/1706.03762", "paper"),
        ("https://arxiv.org/pdf/1706.03762v7", "paper"),
        ("~/papers/attention.pdf", "paper"),
        ("paper.PDF", "paper"),
        ("https://www.youtube.com/playlist?list=PLabc123", "playlist"),
        ("https://youtube.com/playlist?list=PLabc123", "playlist"),
        ("https://m.youtube.com/playlist?list=PLabc123", "playlist"),
        # A watch URL with a list param stays a single video by default.
        ("https://www.youtube.com/watch?v=abc&list=PLabc123", "youtube"),
        # ... but a watch URL with list= and no v= names only the playlist.
        ("https://www.youtube.com/watch?list=PLabc123", "playlist"),
        # youtu.be short links carry the video id in the path.
        ("https://youtu.be/abc?list=PLabc123", "youtube"),
        ("https://github.com/anthropics/claude-code", "repo"),
        ("https://github.com/anthropics/claude-code/", "repo"),
        ("http://github.com/anthropics/claude-code", "repo"),
        # GitHub's UI appends ?tab=... / #readme; hosts are case-insensitive.
        ("https://github.com/psf/requests?tab=readme-ov-file", "repo"),
        ("https://github.com/psf/requests#readme", "repo"),
        ("https://GitHub.com/anthropics/claude-code", "repo"),
        # Deeper GitHub paths are not repo sources; they fall through.
        ("https://github.com/anthropics/claude-code/tree/main/docs", "article"),
        ("https://github.com/anthropics/claude-code/blob/main/README.md", "article"),
        ("https://github.com/anthropics", "article"),
        ("https://example.com/blog-post", "article"),
        ("http://example.com/post.html", "article"),
    ],
)
def test_detect_source(source, expected):
    assert utils.detect_source(source) == expected


def test_detect_source_rejects_unknown():
    with pytest.raises(utils.ExtractError, match="Unsupported source"):
        utils.detect_source("notes.txt")
    with pytest.raises(utils.ExtractError, match="Unsupported source"):
        utils.detect_source("ftp://example.com/doc")


def test_detect_source_epub_is_book():
    assert utils.detect_source("~/books/deep-work.epub") == "book"
    assert utils.detect_source("NOVEL.EPUB") == "book"


def test_detect_source_forced_book_on_pdf():
    assert utils.detect_source("manual.pdf", "book") == "book"


def test_detect_source_forced_matching_type_is_noop():
    assert utils.detect_source("paper.pdf", "paper") == "paper"
    assert utils.detect_source("https://youtu.be/abc", "youtube") == "youtube"
    assert utils.detect_source("novel.epub", "book") == "book"
    assert (
        utils.detect_source("https://www.youtube.com/playlist?list=PL1", "playlist")
        == "playlist"
    )
    assert utils.detect_source("https://github.com/o/r", "repo") == "repo"
    assert utils.detect_source("https://example.com/post", "article") == "article"


def test_detect_source_forced_playlist_on_watch_list_url():
    source = "https://www.youtube.com/watch?v=abc&list=PL1"
    assert utils.detect_source(source) == "youtube"
    assert utils.detect_source(source, "playlist") == "playlist"


def test_detect_source_watch_list_without_video_id_is_playlist():
    # No v= means there is no video for the single-video parser.
    source = "https://www.youtube.com/watch?list=PL1"
    assert utils.detect_source(source) == "playlist"
    assert utils.detect_source(source, "playlist") == "playlist"
    with pytest.raises(utils.ExtractError, match="cannot be extracted as"):
        utils.detect_source(source, "youtube")


def test_detect_source_forced_repo_on_readme_tab_url():
    source = "https://github.com/psf/requests?tab=readme-ov-file"
    assert utils.detect_source(source, "repo") == "repo"


@pytest.mark.parametrize(
    "source",
    [
        "https://youtu.be/abc",
        "https://www.youtube.com/playlist?list=PL1",
        "https://arxiv.org/abs/1706.03762",
        "https://github.com/o/r",
        "https://example.com/post",
    ],
)
def test_detect_source_forced_article_valid_on_any_http_url(source):
    assert utils.detect_source(source, "article") == "article"


@pytest.mark.parametrize(
    "source,forced",
    [
        ("novel.epub", "paper"),
        ("novel.epub", "youtube"),
        ("paper.pdf", "youtube"),
        ("https://youtu.be/abc", "book"),
        ("https://arxiv.org/abs/1706.03762", "book"),
        # playlist needs a list= param on the URL.
        ("https://www.youtube.com/watch?v=abc", "playlist"),
        ("https://example.com/post", "playlist"),
        # repo only fits bare github.com/<owner>/<repo> URLs.
        ("https://example.com/post", "repo"),
        ("https://github.com/o/r/tree/main", "repo"),
        ("https://youtu.be/abc", "repo"),
        # article needs an http(s) URL, and web articles are not books/papers.
        ("paper.pdf", "article"),
        ("novel.epub", "article"),
        ("https://example.com/post", "book"),
        ("https://example.com/post", "paper"),
        ("https://example.com/post", "youtube"),
    ],
)
def test_detect_source_rejects_impossible_forced_type(source, forced):
    with pytest.raises(utils.ExtractError, match="cannot be extracted as"):
        utils.detect_source(source, forced)


def test_detect_source_rejects_unknown_forced_type():
    with pytest.raises(utils.ExtractError, match="Unknown source type"):
        utils.detect_source("paper.pdf", "banana")


def test_estimate_tokens():
    assert utils.estimate_tokens(1000) == 1333


def test_write_outputs(tmp_path):
    work = tmp_path / "work"
    utils.write_outputs(work, "hello world", {"title": "T", "words": 2})
    assert (work / "full_text.txt").read_text(encoding="utf-8") == "hello world"
    meta = json.loads((work / "metadata.json").read_text(encoding="utf-8"))
    assert meta["title"] == "T"


def test_write_manifest_never_publishes_absolute_home_paths(tmp_path, monkeypatch):
    monkeypatch.setattr(utils.Path, "home", lambda: tmp_path)
    book_path = tmp_path / "books" / "progit.epub"
    meta = {
        "source_type": "book", "title": "Pro Git", "origin": str(book_path),
        "est_tokens": 10, "segments": [{"title": "Ch 1"}],
    }
    utils.write_manifest(tmp_path / "w", str(book_path), meta, {"type": None})
    manifest = json.loads((tmp_path / "w" / "source.json").read_text())
    assert manifest["source"] == "~/books/progit.epub"
    assert manifest["origin"] == "~/books/progit.epub"
    assert manifest["est_tokens"] == 10
    assert manifest["options"] == {}
