"""Inventory of the skills source-to-skill made on this machine.

Usage: python3 scripts/library.py [--root PATH ...] [--stale-days N]

Scans the agents' skills folders (user-level and the current project's)
for skill directories holding a source.json manifest, top-level or under
sources/ for topic skills, and prints one JSON object with a `skills`
list: name, path, description, source type, title, origin, extraction
date, token estimate, and whether the skill is due for a refresh.
Read-only: it never writes, fetches, or re-extracts anything.
"""
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

SKILL_ROOTS = (
    "~/.claude/skills", "~/.agents/skills", "~/.copilot/skills",
    "~/.gemini/skills", "~/.cursor/skills", "~/.config/opencode/skills",
    "~/.kiro/skills", "~/.factory/skills", "~/.codeium/windsurf/skills",
    ".claude/skills", ".agents/skills", ".github/skills", ".gemini/skills",
    ".cursor/skills", ".opencode/skills", ".kiro/skills", ".factory/skills",
    ".windsurf/skills",
)

# Sources that keep publishing: a skill made from them goes stale.
GROWING_TYPES = ("playlist", "docs", "thread", "notes", "repo")

DEFAULT_STALE_DAYS = 30

FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)


def _frontmatter(skill_md: Path) -> dict:
    try:
        text = skill_md.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return {}
    match = FRONTMATTER_RE.match(text)
    fields = {}
    block = None  # key of a `>` / `|` block scalar being collected
    for line in (match.group(1) if match else "").splitlines():
        if block and (line.startswith((" ", "\t")) or not line.strip()):
            # Folded and literal blocks are joined into one line.
            if line.strip():
                fields[block] = f"{fields[block]} {line.strip()}".strip()
            continue
        block = None
        key, _, value = line.partition(":")
        if not key.strip() or line.startswith(" "):
            continue
        if re.fullmatch(r"[>|][+-]?", value.strip()):
            block = key.strip()
            fields[block] = ""
        elif value.strip():
            fields[key.strip()] = value.strip()
    return fields


def _load(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _age_days(stamp, now: datetime):
    try:
        then = datetime.strptime(stamp, "%Y-%m-%dT%H:%M:%SZ")
    except (TypeError, ValueError):
        return None
    return (now - then.replace(tzinfo=timezone.utc)).days


def describe(skill_dir: Path, now: datetime, stale_days: int):
    """One inventory entry, or None when the folder is not a made skill."""
    manifests = []
    if (skill_dir / "source.json").is_file():
        manifests.append(_load(skill_dir / "source.json"))
    manifests += [
        _load(path) for path in sorted(skill_dir.glob("sources/*.source.json"))
    ]
    manifests = [m for m in manifests if m.get("source")]
    if not manifests:
        return None
    fields = _frontmatter(skill_dir / "SKILL.md")
    sources = []
    for manifest in manifests:
        age = _age_days(manifest.get("extracted_at"), now)
        sources.append({
            "source_type": manifest.get("source_type"),
            "title": manifest.get("title"),
            "origin": manifest.get("origin") or manifest.get("source"),
            "extracted_at": manifest.get("extracted_at"),
            "age_days": age,
            "est_tokens": manifest.get("est_tokens"),
            "segments": len(manifest.get("segments") or []),
            "refresh_due": (
                manifest.get("source_type") in GROWING_TYPES
                and age is not None and age >= stale_days
            ),
        })
    return {
        "name": fields.get("name") or skill_dir.name,
        "path": str(skill_dir),
        "description": fields.get("description", ""),
        "topic": len(sources) > 1,
        "sources": sources,
        "refresh_due": any(s["refresh_due"] for s in sources),
    }


def scan(roots, now=None, stale_days=DEFAULT_STALE_DAYS) -> list:
    now = now or datetime.now(timezone.utc)
    seen, skills = set(), []
    for root in roots:
        base = Path(root).expanduser()
        if not base.is_dir():
            continue
        for child in sorted(base.iterdir()):
            if not (child / "SKILL.md").is_file():
                continue
            real = child.resolve()
            if real in seen:
                continue
            seen.add(real)
            entry = describe(child, now, stale_days)
            if entry:
                skills.append(entry)
    return skills


def main(argv) -> int:
    roots, stale_days = [], DEFAULT_STALE_DAYS
    args = list(argv)
    while args:
        flag = args.pop(0)
        if flag in ("-h", "--help"):
            print(__doc__)
            return 0
        if flag not in ("--root", "--stale-days") or not args:
            print(__doc__, file=sys.stderr)
            return 2
        value = args.pop(0)
        if flag == "--root":
            roots.append(value)
        elif value.isdigit():
            stale_days = int(value)
        else:
            print("--stale-days needs a whole number.", file=sys.stderr)
            return 2
    skills = scan(roots or SKILL_ROOTS, stale_days=stale_days)
    print(json.dumps({"skills": skills}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
