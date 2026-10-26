import pytest

from extractor import dependencies, transcribe
from extractor.utils import ExtractError


def test_probe_reports_all_configured_deps():
    report = dependencies.probe()
    assert set(report) == {"yt_dlp", "fitz"}
    for entry in report.values():
        assert {"available", "pip", "needed_for"} <= set(entry)


def test_require_returns_module_when_available():
    assert dependencies.require("json").dumps({}) == "{}"


def test_require_raises_with_install_hint(monkeypatch):
    monkeypatch.setitem(
        dependencies.config.OPTIONAL_DEPS,
        "definitely_not_installed",
        {"pip": "definitely-not-installed", "needed_for": "testing"},
    )
    with pytest.raises(ExtractError, match="pip install definitely-not-installed"):
        dependencies.require("definitely_not_installed")


def test_check_report_mentions_every_dep():
    report = dependencies.check_report()
    assert "yt-dlp" in report
    assert "PyMuPDF" in report


def test_require_prefers_modern_pymupdf_name(monkeypatch):
    seen = []

    def fake_import(name):
        seen.append(name)
        return name

    monkeypatch.setattr(dependencies.importlib, "import_module", fake_import)
    assert dependencies.require("fitz") == "pymupdf"
    assert seen == ["pymupdf"]


def test_check_report_flags_installed_but_broken_whisper(monkeypatch):
    """A backend that is installed but fails to import (broken native
    wheel) must not be reported as missing with a reinstall hint."""
    def broken_import(name, *args, **kwargs):
        raise ImportError("dlopen(_spropack.so): zero-fill section")

    monkeypatch.setattr(transcribe.importlib, "import_module", broken_import)
    monkeypatch.setattr(
        transcribe.importlib.util, "find_spec",
        lambda name: object() if name == "mlx_whisper" else None,
    )
    lines = "\n".join(dependencies._transcription_lines())
    assert "BROKEN  mlx-whisper" in lines
    assert "zero-fill section" in lines
    assert "MISSING Whisper" not in lines
