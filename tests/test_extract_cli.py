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


def fake_book_parse(source):
    metadata = {
        "source_type": "book",
        "title": "Fake Book",
        "origin": source,
        "words": 3,
        "est_tokens": 4,
        "segments": [{"title": "Ch 1", "start_s": None, "pages": None, "offset": 0}],
    }
    return "book text", metadata


def test_main_type_book_routes_pdf_to_book_parser(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(config, "work_dir", lambda: tmp_path / "work")
    monkeypatch.setattr(extract.book, "parse", fake_book_parse)
    assert extract.main(["/x/manual.pdf", "--type", "book"]) == 0
    summary = json.loads(capsys.readouterr().out)
    assert summary["source_type"] == "book"
    assert summary["segments"] == 1


def test_main_epub_auto_routes_to_book_parser(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(config, "work_dir", lambda: tmp_path / "work")
    monkeypatch.setattr(extract.book, "parse", fake_book_parse)
    assert extract.main(["/x/novel.epub"]) == 0
    assert json.loads(capsys.readouterr().out)["source_type"] == "book"


def test_main_unknown_type_exits_1(capsys):
    assert extract.main(["x.pdf", "--type", "banana"]) == 1
    assert "Unknown source type" in capsys.readouterr().err


def test_main_incompatible_type_exits_1(capsys):
    assert extract.main(["novel.epub", "--type", "paper"]) == 1
    assert "cannot be extracted as" in capsys.readouterr().err


def test_main_type_without_value_exits_1(capsys):
    assert extract.main(["x.pdf", "--type"]) == 1
    err = capsys.readouterr().err
    assert err.startswith("ERROR")
    assert "--type" in err
