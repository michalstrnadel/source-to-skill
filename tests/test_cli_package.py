"""Tests for the `source-to-skill` console script (src/source_to_skill/cli.py)."""
import sys
from pathlib import Path

import pytest

from source_to_skill import __version__, cli

ROOT = Path(__file__).resolve().parent.parent
SKILL_SRC = ROOT / "skills" / "source-to-skill"


@pytest.fixture
def home(tmp_path, monkeypatch):
    home_dir = tmp_path / "home"
    home_dir.mkdir()
    monkeypatch.setenv("HOME", str(home_dir))
    monkeypatch.setenv("USERPROFILE", str(home_dir))
    return home_dir


def _assert_skill_installed(target: Path):
    assert (target / "SKILL.md").is_file()
    assert (target / "scripts" / "extract.py").is_file()
    assert (target / "tools" / "validate_skill.py").is_file()
    assert not list(target.rglob("__pycache__"))
    assert not list(target.rglob("*.pyc"))


def test_skill_dir_resolves_to_repo_skill():
    assert cli.skill_dir().resolve() == SKILL_SRC.resolve()


def test_install_default_goes_to_claude_home(home, capsys):
    assert cli.main(["install"]) == 0
    target = home / ".claude" / "skills" / "source-to-skill"
    _assert_skill_installed(target)
    out = capsys.readouterr().out
    assert str(target) in out
    assert "/source-to-skill" in out


@pytest.mark.parametrize(
    "agent, rel",
    [("agents", ".agents/skills"), ("copilot", ".copilot/skills")],
)
def test_install_agent_home_dirs(home, agent, rel):
    assert cli.main(["install", "--agent", agent]) == 0
    _assert_skill_installed(home / rel / "source-to-skill")


@pytest.mark.parametrize(
    "agent, rel",
    [
        ("claude", ".claude/skills"),
        ("agents", ".agents/skills"),
        ("copilot", ".github/skills"),
    ],
)
def test_install_project_dirs(home, tmp_path, monkeypatch, agent, rel):
    project = tmp_path / "project"
    project.mkdir()
    monkeypatch.chdir(project)
    assert cli.main(["install", "--project", "--agent", agent]) == 0
    _assert_skill_installed(project / rel / "source-to-skill")
    assert not (home / ".claude").exists()


def test_install_dest(home, tmp_path):
    target = tmp_path / "custom" / "x"
    assert cli.main(["install", "--dest", str(target)]) == 0
    _assert_skill_installed(target)


def test_install_refuses_existing_target(tmp_path, capsys):
    target = tmp_path / "x"
    target.mkdir()
    (target / "keep.txt").write_text("mine", encoding="utf-8")
    assert cli.main(["install", "--dest", str(target)]) == 1
    assert "--force" in capsys.readouterr().err
    assert (target / "keep.txt").read_text(encoding="utf-8") == "mine"
    assert not (target / "SKILL.md").exists()


def test_install_force_replaces(tmp_path):
    target = tmp_path / "x"
    target.mkdir()
    (target / "stale.txt").write_text("old", encoding="utf-8")
    assert cli.main(["install", "--dest", str(target), "--force"]) == 0
    _assert_skill_installed(target)
    assert not (target / "stale.txt").exists()
    # No staging leftovers next to the target.
    assert sorted(p.name for p in tmp_path.iterdir()) == ["x"]


def test_install_force_replaces_symlink_without_touching_its_target(tmp_path):
    real = tmp_path / "real"
    real.mkdir()
    (real / "keep.txt").write_text("mine", encoding="utf-8")
    link = tmp_path / "link"
    link.symlink_to(real, target_is_directory=True)
    assert cli.main(["install", "--dest", str(link), "--force"]) == 0
    assert not link.is_symlink()
    _assert_skill_installed(link)
    assert (real / "keep.txt").exists()


def test_install_skips_pycache(tmp_path, monkeypatch):
    fake = tmp_path / "bundle"
    (fake / "scripts" / "__pycache__").mkdir(parents=True)
    (fake / "tools").mkdir()
    (fake / "SKILL.md").write_text("---\nname: x\n---\n", encoding="utf-8")
    (fake / "scripts" / "extract.py").write_text("", encoding="utf-8")
    (fake / "scripts" / "__pycache__" / "extract.cpython-314.pyc").write_bytes(b"x")
    (fake / "tools" / "validate_skill.py").write_text("", encoding="utf-8")
    monkeypatch.setattr(cli, "skill_dir", lambda: fake)
    target = tmp_path / "out"
    assert cli.main(["install", "--dest", str(target)]) == 0
    _assert_skill_installed(target)


def test_extract_check_passthrough(capsys):
    assert cli.main(["extract", "--check"]) == 0
    assert capsys.readouterr().out.strip()


def test_check_command(capsys):
    assert cli.main(["check"]) == 0
    assert capsys.readouterr().out.strip()


def test_extract_error_exit_code_passthrough(tmp_path, capsys):
    missing = tmp_path / "nope.pdf"
    assert cli.main(["extract", str(missing)]) == 1
    assert "ERROR" in capsys.readouterr().err


def test_validate_passthrough(tmp_path, capsys):
    skill = tmp_path / "tiny-skill"
    skill.mkdir()
    (skill / "SKILL.md").write_text(
        "---\nname: tiny-skill\ndescription: A tiny skill\n---\n"
        "# Tiny\nSee [notes](notes.md)\n",
        encoding="utf-8",
    )
    (skill / "notes.md").write_text("notes\n", encoding="utf-8")
    assert cli.main(["validate", str(skill)]) == 0
    assert "OK: skill is valid" in capsys.readouterr().out


def test_validate_failure_passthrough(tmp_path, capsys):
    skill = tmp_path / "broken"
    skill.mkdir()
    assert cli.main(["validate", str(skill)]) == 1
    assert "FAIL" in capsys.readouterr().out


def test_version(capsys):
    with pytest.raises(SystemExit) as exc:
        cli.main(["--version"])
    assert exc.value.code == 0
    assert capsys.readouterr().out.strip() == f"source-to-skill {__version__}"


@pytest.mark.skipif(sys.version_info < (3, 11), reason="tomllib needs 3.11+")
def test_wheel_config_covers_every_python_folder_in_skill():
    """Every skill folder holding .py files must be listed as a package in
    pyproject.toml, or its modules silently go missing from the wheel."""
    import tomllib

    config = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    setuptools_cfg = config["tool"]["setuptools"]
    assert setuptools_cfg["package-dir"]["source_to_skill.skill"] == (
        "skills/source-to-skill"
    )
    packages = set(setuptools_cfg["packages"])
    for py in SKILL_SRC.rglob("*.py"):
        if "__pycache__" in py.parts:
            continue
        rel = py.parent.relative_to(SKILL_SRC)
        package = ".".join(("source_to_skill", "skill", *rel.parts))
        assert package in packages, f"{py} not shipped: add {package!r}"
    other = [
        p.relative_to(SKILL_SRC).as_posix()
        for p in SKILL_SRC.rglob("*")
        if p.is_file()
        and p.suffix not in (".py", ".pyc")
        and "__pycache__" not in p.parts
        and p.name != ".DS_Store"
    ]
    data = setuptools_cfg["package-data"]["source_to_skill.skill"]
    assert sorted(other) == sorted(data), "non-.py skill files must be package-data"
