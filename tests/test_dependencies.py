import pytest

from extractor import dependencies
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
