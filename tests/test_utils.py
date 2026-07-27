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
    ],
)
def test_detect_source(source, expected):
    assert utils.detect_source(source) == expected


def test_detect_source_rejects_unknown():
    with pytest.raises(utils.ExtractError, match="Unsupported source"):
        utils.detect_source("https://example.com/blog-post")


def test_estimate_tokens():
    assert utils.estimate_tokens(1000) == 1333


def test_write_outputs(tmp_path):
    work = tmp_path / "work"
    utils.write_outputs(work, "hello world", {"title": "T", "words": 2})
    assert (work / "full_text.txt").read_text(encoding="utf-8") == "hello world"
    meta = json.loads((work / "metadata.json").read_text(encoding="utf-8"))
    assert meta["title"] == "T"
