"""Command-line entry point for the source-to-skill package.

The agent skill itself lives in a self-contained folder (SKILL.md + scripts/
+ tools/). In a wheel it is bundled as ``source_to_skill/skill/``; in a
source checkout / editable install it is read from ``skills/source-to-skill/``.
The companion skills (skill-study, skill-eval, skill-library) ship the same
way, as ``source_to_skill/companions/<name_with_underscores>/`` in a wheel.
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

# Installed next to source-to-skill unless --only source-to-skill.
COMPANIONS = ("skill-study", "skill-eval", "skill-library")

# agent -> (user-level skills root relative to $HOME, project-level root
# relative to cwd), from each agent's skills documentation. Codex, Amp,
# Goose and most others read the shared .agents/skills folders.
AGENT_DIRS = {
    "claude": (Path(".claude/skills"), Path(".claude/skills")),
    "agents": (Path(".agents/skills"), Path(".agents/skills")),
    "codex": (Path(".agents/skills"), Path(".agents/skills")),
    "copilot": (Path(".copilot/skills"), Path(".github/skills")),
    "gemini": (Path(".gemini/skills"), Path(".gemini/skills")),
    "cursor": (Path(".cursor/skills"), Path(".cursor/skills")),
    "opencode": (Path(".config/opencode/skills"), Path(".opencode/skills")),
    "kiro": (Path(".kiro/skills"), Path(".kiro/skills")),
    "windsurf": (Path(".codeium/windsurf/skills"), Path(".windsurf/skills")),
    "factory": (Path(".factory/skills"), Path(".factory/skills")),
}

IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo", ".DS_Store")


def skill_dir(name: str = SKILL_NAME) -> Path:
    """Return a bundled skill folder (wheel install or source checkout)."""
    here = Path(__file__).resolve().parent
    wheel = (
        here / "skill" if name == SKILL_NAME
        else here / "companions" / name.replace("-", "_")
    )
    candidates = [
        wheel,  # installed wheel
        here.parent.parent / "skills" / name,  # src/ checkout, editable install
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


def _exists(path: Path) -> bool:
    return path.exists() or path.is_symlink()


def _copy_skill(source: Path, target: Path) -> None:
    """Copy one skill folder to target, replacing whatever is there."""
    target.parent.mkdir(parents=True, exist_ok=True)
    # Copy into a sibling temp dir first, then swap: the old copy is moved
    # aside into the staging dir (a symlink moves as a link, its target is
    # never touched) and restored if the new one cannot take its place,
    # so a failure never leaves a half-replaced or missing skill behind.
    staging = Path(tempfile.mkdtemp(prefix=f".{SKILL_NAME}-", dir=target.parent))
    try:
        staged = staging / "new"
        old = staging / "old"
        shutil.copytree(source, staged, ignore=IGNORE)
        if _exists(target):
            target.rename(old)
        try:
            staged.rename(target)
        except OSError:
            if _exists(old):
                old.rename(target)
            raise
    finally:
        # Deletes the old copy; rmtree removes a moved symlink as a link.
        shutil.rmtree(staging, ignore_errors=True)


def run_install(args: argparse.Namespace) -> int:
    target = install_target(args.agent, args.project, args.dest)
    # --dest names exactly one folder: installing companions into its
    # parent could replace (with --force) unrelated folders there.
    only = args.only or bool(args.dest)
    # Companions go next to source-to-skill, under their own names.
    plan = [(skill_dir(), target)]
    if not only:
        plan += [
            (skill_dir(name), target.parent / name) for name in COMPANIONS
        ]
    existing = [dest for _, dest in plan if _exists(dest)]
    if existing and not args.force:
        print(
            "ERROR: already exists: "
            + ", ".join(str(dest) for dest in existing)
            + ". Re-run with --force to replace "
            + ("it." if len(existing) == 1 else "them."),
            file=sys.stderr,
        )
        return 1
    for source, dest in plan:
        verb = "Replaced" if _exists(dest) else "Installed"
        _copy_skill(source, dest)
        print(f"{verb} {dest.name} {__version__} skill at {dest}")
    print("Next: in your agent, run  /source-to-skill <url-or-file>")
    if not only:
        print("Then:  /skill-study <skill>  ·  /skill-eval <skill>  ·  "
              "/skill-library")
    print("Optional extractors: pip install 'source-to-skill[all]'  "
          "(check with: source-to-skill check)")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="source-to-skill",
        description=(
            "Turn YouTube videos, playlists & channels, podcasts, meetings, "
            "papers, books, articles, GitHub repos, docs sites, notes, Office "
            "files and HN/Reddit threads into AI agent skills."
        ),
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")

    install = sub.add_parser(
        "install",
        help="copy source-to-skill and its companion skills into a skills folder"
    )
    install.add_argument(
        "--agent",
        choices=sorted(AGENT_DIRS),
        default="claude",
        help="target agent: claude (~/.claude/skills, default); "
        "agents or codex (~/.agents/skills, also read by Amp, Goose, Cursor, "
        "Gemini CLI, OpenCode); copilot (~/.copilot/skills); gemini; cursor; "
        "opencode; kiro; windsurf; factory",
    )
    install.add_argument(
        "--project",
        action="store_true",
        help="install into the current project (./.claude/skills, "
        "./.agents/skills, ./.github/skills, ...) instead of your home dir",
    )
    install.add_argument(
        "--dest",
        metavar="PATH",
        help="explicit target directory for source-to-skill; installs "
        "only source-to-skill (implies --only - companion skills are not "
        "installed with --dest)",
    )
    install.add_argument(
        "--only",
        action="store_true",
        help="install only source-to-skill, without skill-study, "
        "skill-eval and skill-library",
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
