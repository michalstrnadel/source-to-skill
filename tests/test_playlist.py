from types import SimpleNamespace

import pytest

from extractor import config
from extractor.parsers import playlist, youtube
from extractor.utils import ExtractError

PLAYLIST_URL = "https://www.youtube.com/playlist?list=PLdemo"


def watch_url(video_id):
    return f"https://www.youtube.com/watch?v={video_id}"


def caption_url(video_id):
    return f"https://captions.example/{video_id}.vtt"


def vtt(*lines):
    cues = "".join(
        f"00:0{i}:00.000 --> 00:0{i}:05.000\n{text}\n\n"
        for i, text in enumerate(lines)
    )
    return f"WEBVTT\n\n{cues}"


def flat_info(entries, title="Widget Course"):
    return {
        "title": title,
        "webpage_url": PLAYLIST_URL,
        "channel": "Widget School",
        "entries": entries,
    }


def flat_entry(video_id, title):
    return {"id": video_id, "url": watch_url(video_id), "title": title}


def video_info(video_id, title, *, with_captions=True):
    captions = (
        {"en": [{"ext": "vtt", "url": caption_url(video_id)}]}
        if with_captions
        else {}
    )
    return {
        "title": title,
        "webpage_url": watch_url(video_id),
        "subtitles": {},
        "automatic_captions": captions,
    }


VIDEOS = [
    ("vid1", "Lesson One", "welcome to widgets"),
    ("vid2", "Lesson Two", "assembling the widget"),
    ("vid3", "Lesson Three", "shipping your widget"),
]


class FakeYDL:
    infos = {}
    opts_seen = []

    def __init__(self, opts):
        self.opts = opts
        FakeYDL.opts_seen.append(opts)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def extract_info(self, url, download=False):
        result = FakeYDL.infos[url]
        if isinstance(result, Exception):
            raise result
        return result


def _install_fakes(monkeypatch, infos, captions):
    FakeYDL.infos = infos
    FakeYDL.opts_seen = []
    monkeypatch.setattr(
        playlist.dependencies, "require",
        lambda module: SimpleNamespace(YoutubeDL=FakeYDL),
    )
    monkeypatch.setattr(youtube, "_fetch", lambda url: captions[url])


def _install_course(monkeypatch, *, captionless=(), broken=()):
    """Install the three-video course; some videos optionally degraded."""
    infos = {PLAYLIST_URL: flat_info([flat_entry(v, t) for v, t, _ in VIDEOS])}
    captions = {}
    for video_id, title, line in VIDEOS:
        if video_id in broken:
            infos[watch_url(video_id)] = RuntimeError("video unavailable")
            continue
        with_captions = video_id not in captionless
        infos[watch_url(video_id)] = video_info(
            video_id, title, with_captions=with_captions
        )
        if with_captions:
            captions[caption_url(video_id)] = vtt(line)
    _install_fakes(monkeypatch, infos, captions)


def test_parse_builds_metadata_and_ordered_segments(monkeypatch):
    _install_course(monkeypatch)
    full_text, meta = playlist.parse(PLAYLIST_URL)
    assert meta["source_type"] == "playlist"
    assert meta["title"] == "Widget Course"
    assert meta["origin"] == PLAYLIST_URL
    assert meta["channel"] == "Widget School"
    assert meta["video_count"] == 3
    assert meta["skipped"] == []
    assert meta["words"] == len(full_text.split())
    assert meta["est_tokens"] > 0
    titles = [s["title"] for s in meta["segments"]]
    assert titles == ["Lesson One", "Lesson Two", "Lesson Three"]
    assert [s["url"] for s in meta["segments"]] == [
        watch_url(v) for v, _, _ in VIDEOS
    ]
    assert all(s["start_s"] is None for s in meta["segments"])
    assert all(s["pages"] is None for s in meta["segments"])
    offsets = [s["offset"] for s in meta["segments"]]
    assert offsets[0] == 0
    assert offsets == sorted(offsets)
    assert len(set(offsets)) == len(offsets)
    for number, seg in enumerate(meta["segments"], start=1):
        lines = full_text[seg["offset"]:].splitlines()
        assert lines[0] == f"=== [{number:02d}] {seg['title']} ==="
        assert lines[1] == seg["url"]
    assert "assembling the widget" in full_text[offsets[1]:offsets[2]]


def test_parse_uses_flat_listing_and_noplaylist_per_video(monkeypatch):
    _install_course(monkeypatch)
    playlist.parse(PLAYLIST_URL)
    flat_opts, *video_opts = FakeYDL.opts_seen
    assert flat_opts["extract_flat"] is True
    assert len(video_opts) == 3
    assert all(opts["noplaylist"] is True for opts in video_opts)


def test_parse_skips_captionless_video_with_warning(monkeypatch, capsys):
    _install_course(monkeypatch, captionless=("vid2",))
    full_text, meta = playlist.parse(PLAYLIST_URL)
    titles = [s["title"] for s in meta["segments"]]
    assert titles == ["Lesson One", "Lesson Three"]
    assert meta["video_count"] == 3
    assert len(meta["skipped"]) == 1
    assert meta["skipped"][0]["title"] == "Lesson Two"
    assert meta["skipped"][0]["url"] == watch_url("vid2")
    assert "captions" in meta["skipped"][0]["reason"]
    # Chunk numbers keep the playlist positions, so the gap stays visible.
    assert "=== [01] Lesson One ===" in full_text
    assert "[02]" not in full_text
    assert "=== [03] Lesson Three ===" in full_text
    err = capsys.readouterr().err
    assert "WARNING" in err
    assert "Lesson Two" in err


def test_parse_skips_video_whose_metadata_fetch_fails(monkeypatch, capsys):
    _install_course(monkeypatch, broken=("vid1",))
    _, meta = playlist.parse(PLAYLIST_URL)
    titles = [s["title"] for s in meta["segments"]]
    assert titles == ["Lesson Two", "Lesson Three"]
    assert len(meta["skipped"]) == 1
    assert meta["skipped"][0]["url"] == watch_url("vid1")
    assert "video unavailable" in meta["skipped"][0]["reason"]
    assert "WARNING" in capsys.readouterr().err


def test_parse_skips_video_when_error_message_is_empty(monkeypatch, capsys):
    # str(ValueError()) == "" - the skip guard must fall back to the
    # exception type name instead of crashing the whole playlist.
    infos = {PLAYLIST_URL: flat_info([flat_entry(v, t) for v, t, _ in VIDEOS])}
    captions = {}
    for video_id, title, line in VIDEOS:
        if video_id == "vid1":
            infos[watch_url(video_id)] = ValueError()
            continue
        infos[watch_url(video_id)] = video_info(video_id, title)
        captions[caption_url(video_id)] = vtt(line)
    _install_fakes(monkeypatch, infos, captions)
    _, meta = playlist.parse(PLAYLIST_URL)
    titles = [s["title"] for s in meta["segments"]]
    assert titles == ["Lesson Two", "Lesson Three"]
    assert meta["skipped"][0]["reason"] == "ValueError"
    err = capsys.readouterr().err
    assert "WARNING" in err
    assert "ValueError" in err


def test_parse_skips_entry_without_url_or_id(monkeypatch, capsys):
    entries = [
        {"title": "Ghost Entry"},  # no url, no id: no address to fetch
        flat_entry("vid2", "Lesson Two"),
    ]
    infos = {
        PLAYLIST_URL: flat_info(entries),
        watch_url("vid2"): video_info("vid2", "Lesson Two"),
    }
    captions = {caption_url("vid2"): vtt("assembling the widget")}
    _install_fakes(monkeypatch, infos, captions)
    _, meta = playlist.parse(PLAYLIST_URL)
    assert [s["title"] for s in meta["segments"]] == ["Lesson Two"]
    assert meta["skipped"] == [
        {
            "title": "Ghost Entry",
            "url": None,
            "reason": "playlist entry has no url or id",
        }
    ]
    # Only the healthy video hits the network; no fabricated watch?v=None.
    assert len(FakeYDL.opts_seen) == 2  # flat listing + vid2
    err = capsys.readouterr().err
    assert "Ghost Entry" in err
    assert "no url or id" in err


def test_parse_empty_playlist_errors(monkeypatch):
    _install_fakes(monkeypatch, {PLAYLIST_URL: flat_info([])}, {})
    with pytest.raises(ExtractError, match="no videos"):
        playlist.parse(PLAYLIST_URL)


def test_parse_all_videos_captionless_errors(monkeypatch):
    _install_course(monkeypatch, captionless=("vid1", "vid2", "vid3"))
    with pytest.raises(ExtractError, match="captions"):
        playlist.parse(PLAYLIST_URL)


def test_parse_warns_over_video_threshold(monkeypatch, capsys):
    count = config.PLAYLIST_WARN_VIDEOS + 1
    entries = [flat_entry(f"v{i}", f"Lesson {i}") for i in range(1, count + 1)]
    infos = {PLAYLIST_URL: flat_info(entries)}
    captions = {}
    for i in range(1, count + 1):
        infos[watch_url(f"v{i}")] = video_info(f"v{i}", f"Lesson {i}")
        captions[caption_url(f"v{i}")] = vtt(f"lesson {i} content")
    _install_fakes(monkeypatch, infos, captions)
    _, meta = playlist.parse(PLAYLIST_URL)
    assert len(meta["segments"]) == count
    err = capsys.readouterr().err
    assert "WARNING" in err
    assert str(count) in err


def test_parse_no_warning_at_video_threshold(monkeypatch, capsys):
    count = config.PLAYLIST_WARN_VIDEOS
    entries = [flat_entry(f"v{i}", f"Lesson {i}") for i in range(1, count + 1)]
    infos = {PLAYLIST_URL: flat_info(entries)}
    captions = {}
    for i in range(1, count + 1):
        infos[watch_url(f"v{i}")] = video_info(f"v{i}", f"Lesson {i}")
        captions[caption_url(f"v{i}")] = vtt(f"lesson {i} content")
    _install_fakes(monkeypatch, infos, captions)
    playlist.parse(PLAYLIST_URL)
    assert capsys.readouterr().err == ""


def test_parse_stops_early_when_rate_limited(monkeypatch):
    infos = {PLAYLIST_URL: flat_info([flat_entry(f"v{i}", f"V{i}") for i in range(6)])}
    for i in range(6):
        infos[watch_url(f"v{i}")] = RuntimeError("HTTP Error 429: Too Many Requests")
    _install_fakes(monkeypatch, infos, {})
    with pytest.raises(ExtractError, match="rate-limiting"):
        playlist.parse(PLAYLIST_URL)
    # Three videos tried, then it stopped instead of hammering the rest.
    assert len(FakeYDL.opts_seen) == 1 + config.RATE_LIMIT_ABORT_AFTER


def test_parse_all_rate_limited_reports_rate_limit_not_captions(monkeypatch):
    infos = {PLAYLIST_URL: flat_info([flat_entry("v1", "V1")])}
    infos[watch_url("v1")] = RuntimeError("HTTP Error 429: Too Many Requests")
    _install_fakes(monkeypatch, infos, {})
    with pytest.raises(ExtractError, match="rate-limiting"):
        playlist.parse(PLAYLIST_URL)
