import json
from pathlib import Path
from types import SimpleNamespace

import pytest

import extract
from extractor import config, dependencies, transcribe, utils
from extractor.parsers import audio, playlist, youtube
from extractor.utils import ExtractError

CUES = [
    {"start_s": 0.0, "text": "welcome to the show"},
    {"start_s": 700.0, "text": "now the second part"},
]


def fake_transcribe(path):
    fake_transcribe.paths.append(Path(path))
    return list(CUES), "en", "mlx-whisper (whisper-tiny)"


@pytest.fixture
def whisper(monkeypatch):
    fake_transcribe.paths = []
    monkeypatch.setattr(transcribe, "transcribe", fake_transcribe)
    monkeypatch.setattr(transcribe, "available_backend", lambda: "mlx_whisper")
    return fake_transcribe


# --- detection -------------------------------------------------------------


@pytest.mark.parametrize(
    "source,expected",
    [
        ("https://www.youtube.com/@3blue1brown", "playlist"),
        ("https://youtube.com/@3blue1brown/videos", "playlist"),
        ("https://www.youtube.com/channel/UCYO_jab_esuFRV4b17AJtAw", "playlist"),
        ("https://www.youtube.com/c/3blue1brown", "playlist"),
        ("https://podcasts.apple.com/us/podcast/x/id1?i=1000", "audio"),
        ("https://cdn.example.com/ep42.mp3", "audio"),
        ("https://cdn.example.com/ep42.M4A?token=abc", "audio"),
        ("~/recordings/standup.m4a", "audio"),
        ("meeting.mp4", "audio"),
        ("https://example.com/episode-42", "article"),
    ],
)
def test_detect_new_source_types(source, expected):
    assert utils.detect_source(source) == expected


def test_any_http_url_can_be_forced_to_audio():
    assert utils.detect_source("https://vimeo.com/123", "audio") == "audio"
    assert utils.detect_source("https://youtu.be/abc", "audio") == "audio"


def test_local_file_cannot_be_forced_to_audio_unless_media():
    with pytest.raises(ExtractError, match="cannot be extracted as audio"):
        utils.detect_source("book.epub", "audio")


# --- CLI options ------------------------------------------------------------


def test_parse_options_all_flags():
    options = extract._parse_options(
        ["--type", "playlist", "--limit", "5", "--transcribe",
         "--work-dir", "/tmp/w"]
    )
    assert options == {
        "type": "playlist", "limit": 5, "transcribe": True,
        "work_dir": "/tmp/w",
    }


@pytest.mark.parametrize(
    "args,message",
    [
        (["--limit", "0"], "positive whole number"),
        (["--limit", "x"], "positive whole number"),
        (["--limit"], "--limit requires a value"),
        (["--work-dir"], "--work-dir requires a value"),
        (["--type", "--limit", "3"], "--type requires a value"),
        (["--bogus"], "Unrecognized arguments"),
    ],
)
def test_parse_options_errors(args, message):
    with pytest.raises(ExtractError, match=message):
        extract._parse_options(args)


def test_limit_rejected_for_non_playlists(capsys):
    assert extract.main(["https://youtu.be/abc", "--limit", "3"]) == 1
    assert "--limit only applies" in capsys.readouterr().err


def test_transcribe_rejected_for_papers(capsys):
    assert extract.main(["paper.pdf", "--transcribe"]) == 1
    assert "--transcribe only applies" in capsys.readouterr().err


def test_main_work_dir_flag_routes_outputs_and_writes_manifest(
    tmp_path, monkeypatch, capsys
):
    seen = {}

    def fake_parse(source, limit=None):
        seen["work_dir"] = config.work_dir()
        seen["limit"] = limit
        return "text", {
            "source_type": "playlist",
            "title": "Course",
            "origin": "https://www.youtube.com/playlist?list=PL1",
            "words": 1,
            "est_tokens": 1,
            "segments": [
                {"title": "L1", "start_s": None, "pages": None, "offset": 0,
                 "url": "https://youtu.be/one"},
            ],
        }

    monkeypatch.setattr(extract.playlist, "parse", fake_parse)
    work = tmp_path / "custom"
    code = extract.main([
        "https://www.youtube.com/playlist?list=PL1", "--limit", "2",
        "--work-dir", str(work),
    ])
    assert code == 0
    assert seen == {"work_dir": work.resolve(), "limit": 2}
    assert json.loads(capsys.readouterr().out)["work_dir"] == str(work.resolve())
    manifest = json.loads((work / "source.json").read_text(encoding="utf-8"))
    assert manifest["source"] == "https://www.youtube.com/playlist?list=PL1"
    assert manifest["options"] == {"limit": 2}
    assert manifest["segments"] == [{"key": "https://youtu.be/one", "title": "L1"}]
    assert manifest["extractor_version"]
    # The override never leaks into later runs.
    assert config.work_dir() != work.resolve()


# --- audio parser -------------------------------------------------------------


def test_local_audio_file_is_transcribed_and_segmented(tmp_path, whisper):
    recording = tmp_path / "team_sync-2026.m4a"
    recording.write_bytes(b"fake audio")
    full_text, meta = audio.parse(str(recording))
    assert whisper.paths == [recording]
    assert recording.exists()  # local files are never deleted
    assert meta["source_type"] == "audio"
    assert meta["title"] == "team sync 2026"
    assert meta["captions"] == "whisper"
    assert meta["transcribed_with"] == "mlx-whisper (whisper-tiny)"
    assert meta["deep_link_template"] is None
    assert [s["start_s"] for s in meta["segments"]] == [0, 600]
    assert "now the second part" in full_text[meta["segments"][1]["offset"]:]


def test_missing_local_audio_file_errors(tmp_path, whisper):
    with pytest.raises(ExtractError, match="Audio file not found"):
        audio.parse(str(tmp_path / "nope.mp3"))


def test_remote_audio_downloads_transcribes_and_cleans_up(
    tmp_path, monkeypatch, whisper
):
    downloaded = tmp_path / "ep.mp3"
    downloaded.write_bytes(b"x")
    info = {
        "title": "Episode 42",
        "webpage_url": "https://cdn.example.com/ep42.mp3",
        "series": "The Show",
        "duration": 900,
        "chapters": [
            {"title": "Cold open", "start_time": 0},
            {"title": "Interview", "start_time": 650},
        ],
    }
    monkeypatch.setattr(audio.dependencies, "require", lambda m: object())
    monkeypatch.setattr(
        "extractor.media.download_audio", lambda ydl, url: (info, downloaded)
    )
    _, meta = audio.parse("https://cdn.example.com/ep42.mp3")
    assert not downloaded.exists()  # downloaded media is removed
    assert meta["channel"] == "The Show"
    assert [s["title"] for s in meta["segments"]] == ["Cold open", "Interview"]
    assert meta["deep_link_template"] == "https://cdn.example.com/ep42.mp3#t={s}"


@pytest.mark.parametrize(
    "origin,template",
    [
        ("https://www.youtube.com/watch?v=abc", "https://www.youtube.com/watch?v=abc&t={s}s"),
        ("https://youtu.be/abc", "https://youtu.be/abc?t={s}s"),
        ("https://vimeo.com/123", "https://vimeo.com/123#t={s}s"),
        ("https://cdn.example.com/a.mp3?x=1", "https://cdn.example.com/a.mp3?x=1#t={s}"),
        ("https://podcasts.apple.com/us/podcast/x/id1?i=2", None),
        ("/Users/me/rec.m4a", None),
    ],
)
def test_deep_link_template(origin, template):
    assert audio.deep_link_template(origin) == template


# --- YouTube whisper fallback -----------------------------------------------


class FakeYDL:
    info = {}

    def __init__(self, opts):
        self.opts = opts

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def extract_info(self, url, download=False):
        return FakeYDL.info


def _captionless_video(monkeypatch, tmp_path):
    FakeYDL.info = {
        "title": "No Captions",
        "webpage_url": "https://www.youtube.com/watch?v=abc",
        "duration": 800,
        "subtitles": {},
        "automatic_captions": {},
    }
    monkeypatch.setattr(
        youtube.dependencies, "require",
        lambda module: SimpleNamespace(YoutubeDL=FakeYDL),
    )
    media = tmp_path / "abc.webm"
    media.write_bytes(b"x")
    monkeypatch.setattr(
        "extractor.media.download_audio", lambda ydl, url: ({}, media)
    )
    return media


def test_captionless_video_falls_back_to_whisper(tmp_path, monkeypatch, whisper):
    media = _captionless_video(monkeypatch, tmp_path)
    _, meta = youtube.parse("https://www.youtube.com/watch?v=abc")
    assert meta["captions"] == "whisper"
    assert whisper.paths == [media]
    assert not media.exists()
    assert meta["deep_link_template"] == "https://www.youtube.com/watch?v=abc&t={s}s"


def test_captionless_video_without_backend_names_install_hint(
    tmp_path, monkeypatch
):
    _captionless_video(monkeypatch, tmp_path)
    with pytest.raises(ExtractError, match="pip install mlx-whisper"):
        youtube.parse("https://www.youtube.com/watch?v=abc")


def test_transcribe_flag_skips_captions(tmp_path, monkeypatch, whisper):
    _captionless_video(monkeypatch, tmp_path)
    FakeYDL.info["automatic_captions"] = {
        "en": [{"ext": "vtt", "url": "https://captions.example/x.vtt"}]
    }
    monkeypatch.setattr(
        youtube, "_fetch", lambda url: pytest.fail("captions fetched")
    )
    _, meta = youtube.parse("https://youtu.be/abc", transcribe=True)
    assert meta["captions"] == "whisper"


# --- channels ---------------------------------------------------------------


@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://www.youtube.com/@3blue1brown", "https://www.youtube.com/@3blue1brown/videos"),
        ("https://www.youtube.com/@3blue1brown/featured", "https://www.youtube.com/@3blue1brown/videos"),
        ("youtube.com/channel/UC123/", "https://youtube.com/channel/UC123/videos"),
    ],
)
def test_channel_videos_url(url, expected):
    assert playlist.channel_videos_url(url) == expected


def test_channel_defaults_to_latest_uploads(monkeypatch, capsys):
    calls = []

    class ChannelYDL(FakeYDL):
        def extract_info(self, url, download=False):
            calls.append((url, self.opts))
            if url.endswith("/videos"):
                return {
                    "title": "Widget School - Videos",
                    "channel": "Widget School",
                    "entries": [
                        {"id": f"v{i}", "title": f"Video {i}"}
                        for i in range(30)
                    ],
                }
            return {
                "title": "Video",
                "subtitles": {},
                "automatic_captions": {
                    "en": [{"ext": "vtt", "url": "https://c.example/x.vtt"}]
                },
            }

    monkeypatch.setattr(
        playlist.dependencies, "require",
        lambda module: SimpleNamespace(YoutubeDL=ChannelYDL),
    )
    monkeypatch.setattr(
        youtube, "_fetch",
        lambda url: "WEBVTT\n\n00:00:01.000 --> 00:00:02.000\nhello\n",
    )
    _, meta = playlist.parse("https://www.youtube.com/@widgets")
    assert calls[0][0] == "https://www.youtube.com/@widgets/videos"
    assert calls[0][1]["playlistend"] == config.CHANNEL_DEFAULT_LIMIT
    assert meta["kind"] == "channel"
    assert meta["title"] == "Widget School"
    assert len(meta["segments"]) == config.CHANNEL_DEFAULT_LIMIT
    assert meta["segments"][0]["captions"] == "auto"
    assert "latest 20 videos" in capsys.readouterr().err


# --- transcribe module --------------------------------------------------------


def test_transcribe_without_backend_errors(monkeypatch):
    with pytest.raises(ExtractError, match="local Whisper backend"):
        transcribe.transcribe("x.mp3")


def test_transcribe_requires_ffmpeg_for_mlx(monkeypatch):
    monkeypatch.setattr(transcribe, "available_backend", lambda: "mlx_whisper")
    monkeypatch.setattr(transcribe.shutil, "which", lambda name: None)
    with pytest.raises(ExtractError, match="brew install ffmpeg"):
        transcribe.transcribe("x.mp3")


def test_transcribe_normalizes_and_dedupes_mlx_output(monkeypatch, capsys):
    calls = {}

    def fake_mlx(path, path_or_hf_repo):
        calls["model"] = path_or_hf_repo
        return {
            "language": "en",
            "segments": [
                {"start": 0.0, "text": "  Hello   world "},
                {"start": 2.0, "text": "Hello world"},
                {"start": 3.5, "text": "   "},
                {"start": 4.0, "text": "Bye."},
            ],
        }

    monkeypatch.setattr(transcribe, "available_backend", lambda: "mlx_whisper")
    monkeypatch.setattr(transcribe.shutil, "which", lambda name: "/bin/ffmpeg")
    monkeypatch.setattr(
        transcribe.importlib, "import_module",
        lambda name: SimpleNamespace(transcribe=fake_mlx),
    )
    monkeypatch.setenv(config.WHISPER_MODEL_ENV, "mlx-community/whisper-tiny")
    cues, language, label = transcribe.transcribe("ep.mp3")
    assert cues == [
        {"start_s": 0.0, "text": "Hello world"},
        {"start_s": 4.0, "text": "Bye."},
    ]
    assert language == "en"
    assert calls["model"] == "mlx-community/whisper-tiny"
    assert label == "mlx-whisper (whisper-tiny)"
    assert "Transcribing ep.mp3" in capsys.readouterr().err


def test_transcribe_faster_whisper_runner():
    class Model:
        def __init__(self, name, device, compute_type):
            self.name = name

        def transcribe(self, path, vad_filter):
            segs = [SimpleNamespace(start=1.0, text="hi")]
            return iter(segs), SimpleNamespace(language="de")

    module = SimpleNamespace(WhisperModel=Model)
    assert transcribe._run_faster(module, "a.mp3", "small") == ([(1.0, "hi")], "de")


def test_transcribe_no_speech_errors(monkeypatch):
    monkeypatch.setattr(transcribe, "available_backend", lambda: "faster_whisper")
    monkeypatch.setitem(
        transcribe.RUNNERS, "faster_whisper", lambda m, p, model: ([], "en")
    )
    monkeypatch.setattr(transcribe.importlib, "import_module", lambda n: None)
    with pytest.raises(ExtractError, match="no speech"):
        transcribe.transcribe("silence.wav")


# --- --check ------------------------------------------------------------------


def test_yt_dlp_age_days():
    from datetime import date

    assert dependencies.yt_dlp_age_days("2026.08.19", date(2026, 10, 4)) == 46
    assert dependencies.yt_dlp_age_days("garbage") is None


def test_check_report_mentions_whisper_install_hint():
    assert "pip install mlx-whisper" in dependencies.check_report()


def test_check_report_warns_on_stale_yt_dlp(monkeypatch):
    monkeypatch.setattr(
        dependencies.importlib, "import_module",
        lambda name: SimpleNamespace(__version__="2020.01.01"),
    )
    assert "pip install -U yt-dlp" in dependencies.check_report()


# --- podcast feeds -------------------------------------------------------------


@pytest.mark.parametrize(
    "source,expected",
    [
        ("https://feeds.megaphone.fm/hubermanlab", "playlist"),
        ("https://feeds.simplecast.com/54nAGcIl", "playlist"),
        ("https://anchor.fm/s/abc123/podcast/rss", "playlist"),
        ("https://example.com/podcast.xml", "playlist"),
        ("https://example.com/blog/feed/", "playlist"),
        ("https://example.com/feedback-wanted", "article"),
    ],
)
def test_detect_podcast_feeds(source, expected):
    assert utils.detect_source(source) == expected


def test_feed_defaults_to_latest_episodes_with_deep_links(
    monkeypatch, capsys, whisper, tmp_path
):
    episodes = [
        {"url": f"https://cdn.example.com/ep{i}.mp3", "title": f"Ep {i}"}
        for i in range(8)
    ]

    class FeedYDL(FakeYDL):
        def extract_info(self, url, download=False):
            if url.endswith("/rss"):
                return {"title": "The Show", "entries": episodes}
            return {"title": url.rsplit("/", 1)[-1], "subtitles": {},
                    "automatic_captions": {}}

    monkeypatch.setattr(
        playlist.dependencies, "require",
        lambda module: SimpleNamespace(YoutubeDL=FeedYDL),
    )
    media = tmp_path / "ep.mp3"

    def fake_download(ydl, url):
        media.write_bytes(b"x")
        return {}, media

    monkeypatch.setattr("extractor.media.download_audio", fake_download)
    _, meta = playlist.parse("https://anchor.fm/s/abc/podcast/rss")
    assert meta["kind"] == "feed"
    assert meta["segments"][0]["title"] == "Ep 0"  # not the file name
    assert len(meta["segments"]) == config.FEED_DEFAULT_LIMIT
    first = meta["segments"][0]
    assert first["captions"] == "whisper"
    assert first["deep_link_template"] == "https://cdn.example.com/ep0.mp3#t={s}"
    assert "latest 5 episodes" in capsys.readouterr().err
    assert len(whisper.paths) == config.FEED_DEFAULT_LIMIT


def test_whisper_fallback_survives_yt_dlp_plugin_rebinding_extractor(
    tmp_path, monkeypatch, whisper
):
    # yt-dlp's plugin loader can replace sys.modules["extractor"] with its
    # own ytdlp_plugins.extractor package once a YoutubeDL starts.
    import sys
    import types

    media_file = _captionless_video(monkeypatch, tmp_path)
    monkeypatch.setitem(
        sys.modules, "extractor", types.ModuleType("ytdlp_plugins.extractor")
    )
    # In a real run the submodule may not be cached yet when that happens.
    monkeypatch.delitem(sys.modules, "extractor.media")
    _, meta = youtube.parse("https://www.youtube.com/watch?v=abc")
    assert meta["captions"] == "whisper"
    assert whisper.paths == [media_file]


def test_download_audio_is_quiet_and_has_no_progress_bar(tmp_path, monkeypatch):
    from extractor import media

    seen = {}
    target = tmp_path / "work" / "media" / "x.mp3"

    class DL:
        def __init__(self, opts):
            seen.update(opts)

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def extract_info(self, url, download):
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(b"x")
            return {"filepath": str(target)}

    monkeypatch.setattr(config, "work_dir", lambda: tmp_path / "work")
    _, path = media.download_audio(SimpleNamespace(YoutubeDL=DL), "https://x/a.mp3")
    assert path == target
    assert seen["quiet"] and seen["noprogress"]
