from pathlib import Path

from extractor.parsers import youtube

FIXTURE = Path(__file__).parent / "fixtures" / "sample.vtt"


def test_parse_vtt_extracts_cues_with_start_seconds():
    cues = youtube.parse_vtt(FIXTURE.read_text(encoding="utf-8"))
    assert cues[0] == {"start_s": 1.0, "text": "welcome to the course"}
    assert {"start_s": 842.0, "text": "now the attention mechanism"} in cues
    assert cues[-1]["start_s"] == 3723.5


def test_parse_vtt_strips_inline_tags():
    cues = youtube.parse_vtt(FIXTURE.read_text(encoding="utf-8"))
    assert {"start_s": 7.5, "text": "today we cover transformers"} in cues


def test_parse_vtt_drops_consecutive_duplicates_and_headers():
    cues = youtube.parse_vtt(FIXTURE.read_text(encoding="utf-8"))
    texts = [c["text"] for c in cues]
    assert texts.count("welcome to the course") == 1
    assert "WEBVTT" not in texts


def test_parse_vtt_unescapes_html_entities():
    vtt = (
        "WEBVTT\n\n"
        "00:00:01.000 --> 00:00:02.000\n"
        "AT&amp;T earnings &gt; expectations\n"
    )
    cues = youtube.parse_vtt(vtt)
    assert cues == [{"start_s": 1.0, "text": "AT&T earnings > expectations"}]


def test_parse_vtt_skips_note_blocks_and_cue_identifiers():
    vtt = (
        "WEBVTT\n\n"
        "00:00:01.000 --> 00:00:02.000\n"
        "real text\n\n"
        "NOTE\n"
        "this comment body should not be transcript\n\n"
        "2\n"
        "00:00:03.000 --> 00:00:04.000\n"
        "more text\n"
    )
    cues = youtube.parse_vtt(vtt)
    assert [c["text"] for c in cues] == ["real text", "more text"]
