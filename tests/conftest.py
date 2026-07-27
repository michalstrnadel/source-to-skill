import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL_DIR = ROOT / "skills" / "source-to-skill"
for sub in ("scripts", "tools"):
    path = str(SKILL_DIR / sub)
    if path not in sys.path:
        sys.path.insert(0, path)
