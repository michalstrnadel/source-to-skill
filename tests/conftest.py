import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL_DIR = ROOT / "skills" / "source-to-skill"
for path in (
    str(SKILL_DIR / "scripts"),
    str(SKILL_DIR / "tools"),
    str(ROOT / "src"),
):
    if path not in sys.path:
        sys.path.insert(0, path)


import pytest


@pytest.fixture(autouse=True)
def no_whisper_backend(monkeypatch):
    """Tests run as if no Whisper backend is installed, unless they opt in.

    The developer's machine may have mlx-whisper or faster-whisper; the
    suite must behave the same everywhere and never load a real model.
    """
    from extractor import transcribe

    monkeypatch.setattr(transcribe, "available_backend", lambda: None)
