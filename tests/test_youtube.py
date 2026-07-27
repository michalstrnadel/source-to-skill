from pathlib import Path
from types import SimpleNamespace

import pytest

from extractor.parsers import youtube
from extractor.utils import ExtractError

FIXTURE = Path(__file__).parent / "fixtures" / "sample.vtt"

INFO = {
    "title": "Transformers Explained",
    "webpage_url": "https://www.youtube.com/watch?v=abc",
    "channel": "AI Channel",
    "upload_date": "20240115",
    "duration": 3730,
    "chapters": [
        {"title": "Intro", "start_time": 0},
        {"title": "Attention", "start_time": 840.0},
    ],
    "subtitles": {},
    "automatic_captions": {
        "en": [
            {"ext": "json3", "url": "https://example.com/subs.json3"},
            {"ext": "vtt", "url": "https://example.com/subs.vtt"},
        ]
    },
}


class FakeYDL:
    def __init__(self, opts):
        self.opts = opts
        FakeYDL.last_opts = opts

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def extract_info(self, url, download=False):
        return self.info


def _install_fakes(monkeypatch, info):
    FakeYDL.info = info
    monkeypatch.setattr(
        youtube.dependencies, "require",
        lambda module: SimpleNamespace(YoutubeDL=FakeYDL),
    )
    monkeypatch.setattr(
        youtube, "_fetch", lambda url: FIXTURE.read_text(encoding="utf-8")
    )


def test_parse_builds_metadata_and_segments(monkeypatch):
    _install_fakes(monkeypatch, INFO)
    full_text, meta = youtube.parse("https://youtu.be/abc")
    assert meta["source_type"] == "youtube"
    assert meta["title"] == "Transformers Explained"
    assert meta["captions"] == "auto"
    assert meta["language"] == "en"
    assert meta["upload_date"] == "20240115"
    assert [s["title"] for s in meta["segments"]] == ["Intro", "Attention"]
    assert meta["words"] == len(full_text.split())
    assert "now the attention mechanism" in full_text


def test_parse_prefers_manual_captions(monkeypatch):
    info = dict(INFO)
    info["subtitles"] = {"cs": [{"ext": "vtt", "url": "https://example.com/cs.vtt"}]}
    _install_fakes(monkeypatch, info)
    _, meta = youtube.parse("https://youtu.be/abc")
    assert meta["captions"] == "manual"
    assert meta["language"] == "cs"


def test_parse_prefers_english_variant_captions(monkeypatch):
    info = dict(INFO)
    info["subtitles"] = {
        "ar": [{"ext": "vtt", "url": "https://example.com/ar.vtt"}],
        "en-US": [{"ext": "vtt", "url": "https://example.com/en-us.vtt"}],
    }
    _install_fakes(monkeypatch, info)
    _, meta = youtube.parse("https://youtu.be/abc")
    assert meta["language"] == "en-US"
    assert meta["captions"] == "manual"


def test_parse_skips_languages_without_vtt_format(monkeypatch):
    info = dict(INFO)
    info["subtitles"] = {
        "aa": [{"ext": "srv1", "url": "https://example.com/aa.srv1"}],
        "de": [{"ext": "vtt", "url": "https://example.com/de.vtt"}],
    }
    info["automatic_captions"] = {}
    _install_fakes(monkeypatch, info)
    _, meta = youtube.parse("https://youtu.be/abc")
    assert meta["language"] == "de"
    assert meta["captions"] == "manual"


def test_parse_sets_noplaylist(monkeypatch):
    _install_fakes(monkeypatch, INFO)
    youtube.parse("https://www.youtube.com/watch?v=abc&list=PL123")
    assert FakeYDL.last_opts["noplaylist"] is True


def test_parse_fails_clearly_without_captions(monkeypatch):
    info = dict(INFO)
    info["subtitles"] = {}
    info["automatic_captions"] = {}
    _install_fakes(monkeypatch, info)
    with pytest.raises(ExtractError, match="No captions available"):
        youtube.parse("https://youtu.be/abc")


def test_parse_fails_on_empty_caption_download(monkeypatch):
    _install_fakes(monkeypatch, INFO)
    monkeypatch.setattr(youtube, "_fetch", lambda url: "WEBVTT\n\n")
    with pytest.raises(ExtractError, match="no cues"):
        youtube.parse("https://youtu.be/abc")
