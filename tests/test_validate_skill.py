import json

import validate_skill


def make_skill(tmp_path, frontmatter, body="# Guide\nSee [notes](notes.md)\n"):
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        f"---\n{frontmatter}\n---\n{body}", encoding="utf-8"
    )
    (skill_dir / "notes.md").write_text("content\n", encoding="utf-8")
    return skill_dir


def test_valid_skill_passes(tmp_path):
    skill_dir = make_skill(tmp_path, "name: my-skill\ndescription: Does things")
    assert validate_skill.validate(skill_dir) == []


def test_name_must_match_directory(tmp_path):
    skill_dir = make_skill(tmp_path, "name: other\ndescription: Does things")
    assert any("!= directory" in e for e in validate_skill.validate(skill_dir))


def test_missing_description_fails(tmp_path):
    skill_dir = make_skill(tmp_path, "name: my-skill")
    assert any("description" in e for e in validate_skill.validate(skill_dir))


def test_broken_link_and_empty_file_fail(tmp_path):
    skill_dir = make_skill(
        tmp_path,
        "name: my-skill\ndescription: Does things",
        body="See [gone](missing.md)\n",
    )
    (skill_dir / "empty.md").write_text("", encoding="utf-8")
    errors = validate_skill.validate(skill_dir)
    assert any("missing.md" in e for e in errors)
    assert any("empty.md" in e for e in errors)


def test_link_check_matches_only_real_markdown_links(tmp_path):
    skill_dir = make_skill(
        tmp_path,
        "name: my-skill\ndescription: Does things",
        body="See [x](gone.md#top) and (mention-only.md)\n",
    )
    errors = validate_skill.validate(skill_dir)
    assert any("gone.md" in e for e in errors)
    assert not any("mention-only.md" in e for e in errors)


def test_missing_skill_md_is_fatal(tmp_path):
    empty_dir = tmp_path / "nothing"
    empty_dir.mkdir()
    errors = validate_skill.validate(empty_dir)
    assert len(errors) == 1 and "SKILL.md" in errors[0]


def _write_evals(skill_dir, data):
    (skill_dir / "evals").mkdir()
    (skill_dir / "evals" / "evals.json").write_text(
        data if isinstance(data, str) else json.dumps(data), encoding="utf-8"
    )


def test_valid_evals_pass(tmp_path):
    skill_dir = make_skill(tmp_path, "name: my-skill\ndescription: Does things")
    _write_evals(skill_dir, {"skill_name": "my-skill", "evals": [
        {"id": 1, "prompt": "Q?", "expected_output": "A",
         "files": [], "expectations": ["Says A"]},
    ]})
    assert validate_skill.validate(skill_dir) == []


def test_skill_without_evals_still_passes(tmp_path):
    skill_dir = make_skill(tmp_path, "name: my-skill\ndescription: Does things")
    assert validate_skill.validate(skill_dir) == []


def test_bad_evals_fail(tmp_path):
    skill_dir = make_skill(tmp_path, "name: my-skill\ndescription: Does things")
    _write_evals(skill_dir, {"skill_name": "other", "evals": [
        {"id": 1, "prompt": "", "expectations": []},
    ]})
    errors = validate_skill.validate(skill_dir)
    assert any("skill_name 'other'" in e for e in errors)
    assert any("eval 1: missing prompt" in e for e in errors)
    assert any("eval 1: no expectations" in e for e in errors)


def test_unparseable_evals_fail(tmp_path):
    skill_dir = make_skill(tmp_path, "name: my-skill\ndescription: Does things")
    _write_evals(skill_dir, "{nope")
    assert any("evals.json" in e for e in validate_skill.validate(skill_dir))


def test_empty_evals_list_fails(tmp_path):
    skill_dir = make_skill(tmp_path, "name: my-skill\ndescription: Does things")
    _write_evals(skill_dir, {"skill_name": "my-skill", "evals": []})
    assert validate_skill.validate(skill_dir) == ["evals/evals.json: no evals"]
