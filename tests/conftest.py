import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for sub in ("scripts", "tools"):
    path = str(ROOT / sub)
    if path not in sys.path:
        sys.path.insert(0, path)
