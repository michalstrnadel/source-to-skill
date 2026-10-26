"""Tests for local .srt/.vtt transcript files (meeting exports, captions)."""
import json

import pytest

import extract
from extractor import config, utils
from extractor.parsers import transcript
from extractor.utils import ExtractError

SRT = """﻿1
00:00:01,000 --> 00:00:04,000
Alice Chen: Let's start with the roadmap.

2
00:00:05,500 --> 00:00:08,000
Bob: I think we should <i>ship</i> the beta
in March.

3
00:00:40,000 --> 00:00:44,000
{\\an8}Alice Chen: Agreed. Bob owns the launch checklist.

4
00:11:00,000 --> 00:11:05,250
[MUSIC]

5
00:11:06,000 --> 00:11:07,000
Note: one-off label prefixes are not speakers.

6
00:11:07,500 --> 00:11:09,000
Bob: Sounds good.
"""

TEAMS_VTT = """WEBVTT
Language: de

0f2a-1/12-0
00:00:02.000 --> 00:00:04.500
<v Dana Smith>Morning everyone.</v>

0f2a-1/13-0
00:00:05.000 --> 00:00:07.000
<v.loud Erik>Budget is approved.</v>

NOTE this is a comment
spanning lines

00:00:08.000 --> 00:00:09.000
<v Dana Smith>Great, then we go.</v>
"""


def _write(tmp_path, name, text):
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


def test_srt_cues_keep_speakers_and_follow_the_av_contract(tmp_path):
    path = _write(tmp_path, "weekly_sync-2026-10-01.srt", SRT)
    full_text, meta = transcript.parse(str(path))
    assert meta["source_type"] == "transcript"
    assert meta["format"] == "srt"
    assert meta["title"] == "weekly sync 2026 10 01"
    assert meta["captions"] == "file"
    assert meta["deep_link_template"] is None
    assert meta["duration_s"] == 669  # last cue end, 00:11:09
    assert meta["speakers"] == ["Alice Chen", "Bob"]
    assert meta["origin"] == str(path)
    assert meta["est_tokens"] == utils.estimate_tokens(meta["words"])
    # 10-minute windows like captionless videos: Part 1, Part 2.
    assert [(s["title"], s["start_s"]) for s in meta["segments"]] == [
        ("Part 1", 0), ("Part 2", config.DEFAULT_SEGMENT_WINDOW_S),
    ]
    assert full_text.startswith("=== Part 1 [t=0s] ===\n")
    assert "Alice Chen: Let's start with the roadmap." in full_text
    # Formatting tags and SSA overrides are stripped; continuation lines
    # stay with their cue; inline [t=Ns] markers appear like for videos.
    assert "Bob: I think we should ship the beta" in full_text
    assert "in March." in full_text
    assert "[t=40s] Alice Chen: Agreed. Bob owns the launch checklist." in full_text
    assert "[MUSIC]" not in full_text
    assert "\\an8" not in full_text
    for seg in meta["segments"]:
        assert full_text[seg["offset"]:].startswith(f"=== {seg['title']}")


def test_vtt_voice_tags_become_speaker_prefixes(tmp_path):
    path = _write(tmp_path, "standup.vtt", TEAMS_VTT)
    full_text, meta = transcript.parse(str(path))
    assert meta["format"] == "vtt"
    assert meta["language"] == "de"
    assert meta["speakers"] == ["Dana Smith", "Erik"]
    assert "Dana Smith: Morning everyone." in full_text
    assert "Erik: Budget is approved." in full_text
    assert "comment" not in full_text
    assert [s["title"] for s in meta["segments"]] == ["Part 1"]


def test_short_meeting_is_one_part(tmp_path):
    path = _write(tmp_path, "standup.vtt", TEAMS_VTT)
    _, meta = transcript.parse(str(path))
    assert meta["duration_s"] == 9
    assert len(meta["segments"]) == 1


def test_latin1_file_still_reads(tmp_path):
    path = tmp_path / "old.srt"
    path.write_bytes(
        (
            "1\n00:00:01,000 --> 00:00:02,000\nJosé: café\n\n"
            "2\n00:00:03,000 --> 00:00:04,000\nJosé: crème\n"
        ).encode("latin-1")
    )
    full_text, meta = transcript.parse(str(path))
    assert "José: café" in full_text
    assert meta["speakers"] == ["José"]


def test_errors(tmp_path):
    with pytest.raises(ExtractError, match="not found"):
        transcript.parse(str(tmp_path / "missing.srt"))
    empty = _write(tmp_path, "empty.vtt", "WEBVTT\n\n")
    with pytest.raises(ExtractError, match="no cues"):
        transcript.parse(str(empty))
    with pytest.raises(ExtractError, match="local files"):
        transcript.parse("https://example.com/captions.vtt")


@pytest.mark.parametrize("source", ["meeting.srt", "~/Downloads/Talk.VTT"])
def test_detect_transcript(source):
    assert utils.detect_source(source) == "transcript"


def test_cli_writes_outputs(tmp_path, capsys):
    path = _write(tmp_path, "standup.vtt", TEAMS_VTT)
    work = tmp_path / "work"
    assert extract.main([str(path), "--work-dir", str(work)]) == 0
    meta = json.loads((work / "metadata.json").read_text())
    assert meta["source_type"] == "transcript"
    assert "Erik: Budget is approved." in (work / "full_text.txt").read_text()
    assert json.loads(capsys.readouterr().out)["segments"] == 1


def test_repeated_lines_in_a_transcript_file_are_kept(tmp_path):
    # A real conversation repeats itself; only auto-captions roll lines.
    path = _write(tmp_path, "call.srt", (
        "1\n00:00:01,000 --> 00:00:02,000\nYes.\n\n"
        "2\n00:00:03,000 --> 00:00:04,000\nYes.\n"
    ))
    full_text, _ = transcript.parse(str(path))
    assert full_text.count("Yes.") == 2


def test_cp1252_file_reads_windows_punctuation(tmp_path):
    path = tmp_path / "win.srt"
    path.write_bytes(
        "1\n00:00:01,000 --> 00:00:02,000\nIt’s “quoted” – €5\n".encode(
            "cp1252"
        )
        + b"\n2\n00:00:03,000 --> 00:00:04,000\nbad \x81 byte\n"
    )
    full_text, _ = transcript.parse(str(path))
    assert "It’s “quoted” – €5" in full_text
    assert "bad � byte" in full_text
