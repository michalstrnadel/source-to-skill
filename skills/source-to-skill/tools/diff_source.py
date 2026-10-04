"""Compare a skill's source.json with a fresh extraction.

Usage: python3 tools/diff_source.py <skill-dir> <work-dir>

<skill-dir>/source.json is the manifest copied into the skill when it was
generated; <work-dir>/source.json comes from re-running extract.py on the
same origin. Prints JSON: which segments (videos, chapters, sections) are
new, which disappeared, and how many are unchanged - so a refresh only
generates what is new.
"""
import json
import sys
from pathlib import Path


def _load(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SystemExit(f"ERROR: {path} not found") from None
    except json.JSONDecodeError as err:
        raise SystemExit(f"ERROR: {path} is not valid JSON ({err})") from None


def diff(old: dict, new: dict) -> dict:
    old_keys = [seg["key"] for seg in old.get("segments", [])]
    seen = set(old_keys)
    fresh = {seg["key"] for seg in new.get("segments", [])}
    return {
        "origin": new.get("origin"),
        "source_type": new.get("source_type"),
        "previously_extracted_at": old.get("extracted_at"),
        "added": [
            {"position": index, **seg}
            for index, seg in enumerate(new.get("segments", []), start=1)
            if seg["key"] not in seen
        ],
        "removed": [
            seg for seg in old.get("segments", []) if seg["key"] not in fresh
        ],
        "unchanged": len(seen & fresh),
    }


def main(argv) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 2
    old = _load(Path(argv[0]) / "source.json")
    new = _load(Path(argv[1]) / "source.json")
    if old.get("origin") != new.get("origin"):
        print(
            f"ERROR: origins differ: {old.get('origin')} vs "
            f"{new.get('origin')} - re-extract the skill's own origin.",
            file=sys.stderr,
        )
        return 1
    print(json.dumps(diff(old, new), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
