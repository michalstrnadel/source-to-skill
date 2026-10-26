"""Tests for the skill-library inventory script (skills/skill-library)."""
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "skills" / "skill-library" / "scripts" / "library.py"

spec = importlib.util.spec_from_file_location("_sts_library", SCRIPT)
library = importlib.util.module_from_spec(spec)
spec.loader.exec_module(library)

NOW = datetime(2026, 10, 26, tzinfo=timezone.utc)


def _skill(root: Path, name: str, manifest=None, topic=None) -> Path:
    skill = root / name
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: About {name}\n---\n# {name}\n",
        encoding="utf-8",
    )
    if manifest is not None:
        (skill / "source.json").write_text(json.dumps(manifest), encoding="utf-8")
    for index, item in enumerate(topic or [], 1):
        (skill / "sources").mkdir(exist_ok=True)
        (skill / "sources" / f"{index:02d}-x.source.json").write_text(
            json.dumps(item), encoding="utf-8"
        )
    return skill


def _manifest(kind="youtube", stamp="2026-10-20T10:00:00Z", **extra):
    return {
        "source": "https://example.com/x", "source_type": kind,
        "title": "X", "extracted_at": stamp, "est_tokens": 1200,
        "segments": [{"key": "a", "title": "A"}], **extra,
    }


def test_lists_only_skills_with_a_manifest(tmp_path):
    _skill(tmp_path, "made", _manifest())
    _skill(tmp_path, "handwritten")
    skills = library.scan([tmp_path], now=NOW)
    assert [s["name"] for s in skills] == ["made"]
    entry = skills[0]
    assert entry["description"] == "About made"
    assert entry["sources"][0]["age_days"] == 5
    assert entry["sources"][0]["segments"] == 1
    assert entry["refresh_due"] is False


def test_growing_sources_past_threshold_are_due(tmp_path):
    _skill(tmp_path, "course", _manifest("playlist", "2026-09-01T00:00:00Z"))
    _skill(tmp_path, "talk", _manifest("youtube", "2026-01-01T00:00:00Z"))
    due = {s["name"]: s["refresh_due"] for s in library.scan([tmp_path], now=NOW)}
    assert due == {"course": True, "talk": False}


def test_stale_days_threshold(tmp_path):
    _skill(tmp_path, "course", _manifest("playlist", "2026-10-16T00:00:00Z"))
    assert library.scan([tmp_path], now=NOW)[0]["refresh_due"] is False
    assert library.scan([tmp_path], now=NOW, stale_days=7)[0]["refresh_due"]


def test_topic_skill_reads_sources_folder(tmp_path):
    _skill(tmp_path, "topic", topic=[_manifest("paper"), _manifest("article")])
    entry = library.scan([tmp_path], now=NOW)[0]
    assert entry["topic"] is True
    assert [s["source_type"] for s in entry["sources"]] == ["paper", "article"]


def test_symlinked_skill_listed_once_and_bad_json_ignored(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    real = _skill(a, "made", _manifest())
    b.mkdir()
    (b / "made").symlink_to(real, target_is_directory=True)
    broken = _skill(a, "broken")
    (broken / "source.json").write_text("{not json", encoding="utf-8")
    assert [s["name"] for s in library.scan([a, b], now=NOW)] == ["made"]


def test_missing_roots_and_cli(tmp_path, capsys):
    _skill(tmp_path, "made", _manifest())
    assert library.main(["--root", str(tmp_path / "nope"), "--root", str(tmp_path)]) == 0
    out = json.loads(capsys.readouterr().out)
    assert [s["name"] for s in out["skills"]] == ["made"]
    assert library.main(["--stale-days", "x"]) == 2


def _skill_md(tmp_path, text: bytes) -> Path:
    skill = tmp_path / "s"
    skill.mkdir()
    (skill / "SKILL.md").write_bytes(text)
    return skill / "SKILL.md"


def test_frontmatter_with_crlf_line_endings(tmp_path):
    path = _skill_md(
        tmp_path, b"---\r\nname: s\r\ndescription: Windows file\r\n---\r\n# s\r\n"
    )
    assert library._frontmatter(path) == {
        "name": "s", "description": "Windows file",
    }


@pytest.mark.parametrize("marker", [">", "|", ">-", "|+"])
def test_frontmatter_folded_and_literal_descriptions(tmp_path, marker):
    path = _skill_md(tmp_path, (
        f"---\nname: s\ndescription: {marker}\n  Use when the user\n"
        "  asks about X.\n\nlicense: MIT\n---\n# s\n"
    ).encode())
    fields = library._frontmatter(path)
    assert fields["description"] == "Use when the user asks about X."
    assert fields["license"] == "MIT"
