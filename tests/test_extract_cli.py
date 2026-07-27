import json

from extractor import config
import extract


def fake_parse(source):
    metadata = {
        "source_type": "youtube",
        "title": "Fake",
        "origin": source,
        "words": 2,
        "est_tokens": 2,
        "segments": [{"title": "All", "start_s": 0, "pages": None, "offset": 0}],
    }
    return "fake text", metadata


def test_main_writes_outputs_and_prints_summary(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(config, "work_dir", lambda: tmp_path / "work")
    monkeypatch.setattr(extract.youtube, "parse", fake_parse)
    code = extract.main(["https://youtu.be/abc"])
    assert code == 0
    assert (tmp_path / "work" / "full_text.txt").read_text(encoding="utf-8") == "fake text"
    meta = json.loads((tmp_path / "work" / "metadata.json").read_text(encoding="utf-8"))
    assert meta["title"] == "Fake"
    summary = json.loads(capsys.readouterr().out)
    assert summary["segments"] == 1
    assert summary["work_dir"].endswith("work")


def test_main_check_reports_dependencies(capsys):
    assert extract.main(["--check"]) == 0
    assert "yt-dlp" in capsys.readouterr().out


def test_main_unsupported_source_exits_1(capsys):
    assert extract.main(["https://example.com/post"]) == 1
    assert "Unsupported source" in capsys.readouterr().err


def test_main_reports_unexpected_errors_cleanly(monkeypatch, capsys):
    def boom(source):
        raise RuntimeError("connection refused")

    monkeypatch.setattr(extract.youtube, "parse", boom)
    assert extract.main(["https://youtu.be/abc"]) == 1
    err = capsys.readouterr().err
    assert err.startswith("ERROR")
    assert "connection refused" in err


def test_main_no_args_prints_usage(capsys):
    assert extract.main([]) == 0
    assert "Usage" in capsys.readouterr().out
