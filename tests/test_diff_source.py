import json

import diff_source


def manifest(keys, origin="https://www.youtube.com/playlist?list=PL1"):
    return {
        "origin": origin,
        "source_type": "playlist",
        "extracted_at": "2026-10-01T00:00:00Z",
        "segments": [{"key": k, "title": k.upper()} for k in keys],
    }


def write(dir_path, data):
    dir_path.mkdir(parents=True, exist_ok=True)
    (dir_path / "source.json").write_text(json.dumps(data), encoding="utf-8")
    return dir_path


def test_diff_reports_added_removed_and_unchanged():
    result = diff_source.diff(manifest(["a", "b", "c"]), manifest(["a", "c", "d"]))
    assert result["added"] == [{"position": 3, "key": "d", "title": "D"}]
    assert result["removed"] == [{"key": "b", "title": "B"}]
    assert result["unchanged"] == 2
    assert result["previously_extracted_at"] == "2026-10-01T00:00:00Z"


def test_main_prints_json(tmp_path, capsys):
    skill = write(tmp_path / "skill", manifest(["a"]))
    work = write(tmp_path / "work", manifest(["a", "b"]))
    assert diff_source.main([str(skill), str(work)]) == 0
    out = json.loads(capsys.readouterr().out)
    assert [item["key"] for item in out["added"]] == ["b"]


def test_main_rejects_different_origins(tmp_path, capsys):
    skill = write(tmp_path / "skill", manifest(["a"]))
    work = write(tmp_path / "work", manifest(["a"], origin="https://other"))
    assert diff_source.main([str(skill), str(work)]) == 1
    assert "origins differ" in capsys.readouterr().err


def test_main_missing_manifest_exits(tmp_path):
    import pytest

    with pytest.raises(SystemExit, match="not found"):
        diff_source.main([str(tmp_path / "a"), str(tmp_path / "b")])


def test_main_usage(capsys):
    assert diff_source.main([]) == 2
    assert "Usage" in capsys.readouterr().out
