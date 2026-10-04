"""The release version must be identical everywhere it is declared."""
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
VERSION_RE = re.compile(r'^__version__\s*=\s*["\']([^"\']+)["\']', re.MULTILINE)


def _pyproject_version() -> str:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    assert match, "pyproject.toml: no version"
    return match.group(1)


def _dunder_version(path: Path):
    match = VERSION_RE.search(path.read_text(encoding="utf-8"))
    return match.group(1) if match else None


def test_plugin_json_matches_pyproject():
    plugin = json.loads(
        (ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
    )
    assert plugin["version"] == _pyproject_version()


def test_package_init_matches_pyproject():
    path = ROOT / "src" / "source_to_skill" / "__init__.py"
    assert _dunder_version(path) == _pyproject_version()


def test_extractor_init_matches_pyproject():
    path = ROOT / "skills" / "source-to-skill" / "scripts" / "extractor" / "__init__.py"
    version = _dunder_version(path)
    if version is None:
        pytest.skip(f"{path.relative_to(ROOT)} does not declare __version__ yet")
    assert version == _pyproject_version()
