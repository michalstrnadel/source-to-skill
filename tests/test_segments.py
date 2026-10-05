from extractor.parsers import youtube


def test_build_segments_uses_video_chapters():
    chapters = [
        {"title": "Intro", "start_time": 0},
        {"title": "Attention", "start_time": 840.0},
    ]
    segments = youtube.build_segments(chapters, duration_s=3700)
    assert segments == [
        {"title": "Intro", "start_s": 0},
        {"title": "Attention", "start_s": 840},
    ]


def test_build_segments_with_single_chapter():
    segments = youtube.build_segments(
        [{"title": "Everything", "start_time": 0}], duration_s=3700
    )
    assert segments == [{"title": "Everything", "start_s": 0}]


def test_build_segments_falls_back_to_10_minute_windows():
    segments = youtube.build_segments(None, duration_s=1500)
    assert segments == [
        {"title": "Part 1", "start_s": 0},
        {"title": "Part 2", "start_s": 600},
        {"title": "Part 3", "start_s": 1200},
    ]


def test_build_segments_without_duration_gives_single_segment():
    assert youtube.build_segments(None, duration_s=None) == [
        {"title": "Full transcript", "start_s": 0}
    ]


def test_segment_text_assigns_cues_and_records_offsets():
    cues = [
        {"start_s": 1.0, "text": "hello"},
        {"start_s": 850.0, "text": "attention matters"},
    ]
    segments = [
        {"title": "Intro", "start_s": 5},   # first segment always absorbs from t=0
        {"title": "Attention", "start_s": 840},
    ]
    full_text, out = youtube.segment_text(cues, segments)
    assert "=== Intro [t=5s] ===" in full_text
    assert "hello" in full_text
    assert full_text.index("hello") < full_text.index("attention matters")
    assert out[0]["offset"] == 0
    assert full_text[out[1]["offset"]:].startswith("=== Attention")
    assert out[1] == {
        "title": "Attention",
        "start_s": 840,
        "pages": None,
        "offset": out[1]["offset"],
    }


def test_segment_text_marks_timestamps_inside_long_segments(monkeypatch):
    monkeypatch.setattr(youtube.config, "INLINE_TIMESTAMP_EVERY_S", 60)
    cues = [
        {"start_s": 0.0, "text": "a"},
        {"start_s": 30.0, "text": "b"},
        {"start_s": 61.5, "text": "c"},
        {"start_s": 90.0, "text": "d"},
        {"start_s": 125.0, "text": "e"},
    ]
    full_text, _ = youtube.segment_text(cues, [{"title": "All", "start_s": 0}])
    assert full_text.strip().splitlines()[1:] == [
        "a", "b", "[t=61s] c", "d", "[t=125s] e",
    ]
