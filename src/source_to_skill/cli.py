"""Command-line entry point for the source-to-skill package.

The agent skill itself lives in a self-contained folder (SKILL.md + scripts/
+ tools/). In a wheel it is bundled as ``source_to_skill/skill/``; in a
source checkout / editable install it is read from ``skills/source-to-skill/``.
"""
from __future__ import annotations

import argparse
import importlib.util
import shutil
import sys
import tempfile
from pathlib import Path

from source_to_skill import __version__

SKILL_NAME = "source-to-skill"

# agent -> (user-level skills root relative to $HOME, project-level root relative to cwd)
AGENT_DIRS = {
    "claude": (Path(".claude") / "skills", Path(".claude") / "skills"),
    "agents": (Path(".agents") / "skills", Path(".agents") / "skills"),
    "copilot": (Path(".copilot") / "skills", Path(".github") / "skills"),
}

IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo", ".DS_Store")


def skill_dir() -> Path:
    """Return the bundled skill folder (wheel install or source checkout)."""
    here = Path(__file__).resolve().parent
    candidates = [
        here / "skill",  # installed wheel
        here.parent.parent / "skills" / SKILL_NAME,  # src/ checkout, editable install
    ]
    for candidate in candidates:
        if (candidate / "SKILL.md").is_file():
            return candidate
    raise FileNotFoundError(
        "bundled skill not found; looked in: "
        + ", ".join(str(c) for c in candidates)
    )


def _load_module(path: Path, name: str):
    """Import a bundled script by path with its folder on sys.path."""
    folder = str(path.parent)
    if folder not in sys.path:
        sys.path.insert(0, folder)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_extract(argv: list[str]) -> int:
    module = _load_module(skill_dir() / "scripts" / "extract.py", "_sts_extract")
    return int(module.main(list(argv)) or 0)


def run_validate(argv: list[str]) -> int:
    module = _load_module(
        skill_dir() / "tools" / "validate_skill.py", "_sts_validate_skill"
    )
    return int(module.main(list(argv)) or 0)


def install_target(agent: str, project: bool, dest: str | None) -> Path:
    if dest:
        return Path(dest).expanduser().absolute()
    user_root, project_root = AGENT_DIRS[agent]
    base = Path.cwd() / project_root if project else Path.home() / user_root
    return base / SKILL_NAME


def run_install(args: argparse.Namespace) -> int:
    source = skill_dir()
    target = install_target(args.agent, args.project, args.dest)
    exists = target.exists() or target.is_symlink()
    if exists and not args.force:
        print(
            f"ERROR: {target} already exists. "
            "Re-run with --force to replace it.",
            file=sys.stderr,
        )
        return 1
    target.parent.mkdir(parents=True, exist_ok=True)
    # Copy into a sibling temp dir first so a failed copy never leaves a
    # half-replaced skill behind.
    staging = Path(tempfile.mkdtemp(prefix=f".{SKILL_NAME}-", dir=target.parent))
    try:
        staged = staging / SKILL_NAME
        shutil.copytree(source, staged, ignore=IGNORE)
        if exists:
            if target.is_symlink() or target.is_file():
                target.unlink()
            else:
                shutil.rmtree(target)
        staged.rename(target)
    finally:
        shutil.rmtree(staging, ignore_errors=True)
    verb = "Replaced" if exists else "Installed"
    print(f"{verb} source-to-skill {__version__} skill at {target}")
    print("Next: in your agent, run  /source-to-skill <url-or-file>")
    print("Optional extractors: pip install 'source-to-skill[all]'  "
          "(check with: source-to-skill check)")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="source-to-skill",
        description=(
            "Turn YouTube videos, playlists & channels, podcasts, papers, "
            "books, articles and GitHub repos into AI agent skills."
        ),
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")

    install = sub.add_parser(
        "install", help="copy the source-to-skill agent skill into a skills folder"
    )
    install.add_argument(
        "--agent",
        choices=sorted(AGENT_DIRS),
        default="claude",
        help="target agent: claude (~/.claude/skills, default), "
        "agents (~/.agents/skills), copilot (~/.copilot/skills)",
    )
    install.add_argument(
        "--project",
        action="store_true",
        help="install into the current project (./.claude/skills, "
        "./.agents/skills or ./.github/skills) instead of your home dir",
    )
    install.add_argument(
        "--dest", metavar="PATH", help="explicit full target directory"
    )
    install.add_argument(
        "--force", action="store_true", help="replace an existing install"
    )

    sub.add_parser(
        "extract",
        help="run the extractor: extract <source> [--type TYPE] | --check",
        add_help=False,
    )
    sub.add_parser("check", help="report which optional extractors are available")
    validate = sub.add_parser("validate", help="validate a generated skill folder")
    validate.add_argument("skill_dir", help="path to the skill directory")
    return parser


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    # `extract` forwards everything verbatim (incl. --check / --type / -h).
    if argv and argv[0] == "extract":
        return run_extract(argv[1:])
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "install":
        return run_install(args)
    if args.command == "check":
        return run_extract(["--check"])
    if args.command == "validate":
        return run_validate([args.skill_dir])
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
