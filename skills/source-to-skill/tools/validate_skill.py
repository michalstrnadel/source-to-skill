"""Validate a generated skill directory.

Usage: python3 tools/validate_skill.py <skill-dir>

Checks: SKILL.md exists with YAML frontmatter containing name (matching the
directory) and description (<= 1024 chars); every relative .md link in
SKILL.md resolves; no .md file in the skill is empty; evals/evals.json,
when present, parses and gives every eval a prompt and expectations.
"""
import json
import re
import sys
from pathlib import Path

FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
# Real markdown links only ([label](target.md) or [label](target.md#anchor));
# a bare parenthetical like "(notes.md)" in prose is not a link.
MD_LINK_RE = re.compile(r"\[[^\]]*\]\(([\w./-]+\.md)(?:#[^)\s]*)?\)")


def _parse_frontmatter(block: str) -> dict:
    fields = {}
    for line in block.splitlines():
        key, _, value = line.partition(":")
        if key.strip() and value.strip():
            fields[key.strip()] = value.strip()
    return fields


def validate(skill_dir: Path) -> list[str]:
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        return [f"missing {skill_md}"]
    errors = []
    text = skill_md.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(text)
    if not match:
        errors.append("SKILL.md: missing YAML frontmatter")
    else:
        fields = _parse_frontmatter(match.group(1))
        name = fields.get("name")
        if not name:
            errors.append("frontmatter: missing name")
        elif name != skill_dir.name:
            errors.append(
                f"frontmatter name '{name}' != directory '{skill_dir.name}'"
            )
        description = fields.get("description", "")
        if not description:
            errors.append("frontmatter: missing description")
        elif len(description) > 1024:
            errors.append("frontmatter: description over 1024 chars")
    for ref in MD_LINK_RE.findall(text):
        if not (skill_dir / ref).is_file():
            errors.append(f"SKILL.md links to missing file: {ref}")
    for md_file in sorted(skill_dir.rglob("*.md")):
        if not md_file.read_text(encoding="utf-8").strip():
            errors.append(f"empty file: {md_file.relative_to(skill_dir)}")
    errors += _validate_evals(skill_dir)
    return errors


def _validate_evals(skill_dir: Path) -> list[str]:
    """Check evals/evals.json (skill-creator format) when the skill has one."""
    path = skill_dir / "evals" / "evals.json"
    if not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except ValueError as err:
        return [f"evals/evals.json: not valid JSON ({err})"]
    if not isinstance(data, dict) or not isinstance(data.get("evals"), list):
        return ["evals/evals.json: needs an \"evals\" list"]
    if not data["evals"]:
        return ["evals/evals.json: no evals"]
    errors = []
    if data.get("skill_name") != skill_dir.name:
        errors.append(
            f"evals/evals.json: skill_name '{data.get('skill_name')}' "
            f"!= directory '{skill_dir.name}'"
        )
    for index, item in enumerate(data["evals"], 1):
        if not isinstance(item, dict):
            errors.append(f"evals/evals.json: eval {index} is not an object")
            continue
        label = f"evals/evals.json: eval {item.get('id', index)}"
        if not str(item.get("prompt", "")).strip():
            errors.append(f"{label}: missing prompt")
        if not item.get("expectations"):
            errors.append(f"{label}: no expectations")
    return errors


def main(argv) -> int:
    if len(argv) != 1:
        print(__doc__)
        return 2
    errors = validate(Path(argv[0]))
    if errors:
        print("\n".join(f"FAIL: {error}" for error in errors))
        return 1
    print("OK: skill is valid")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
