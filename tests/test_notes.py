"""Tests for the local notes-folder parser (Obsidian vaults, Markdown folders)."""
import pytest

from extractor import config
from extractor.parsers import notes
from extractor.utils import ExtractError


def _write(root, rel, text):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


@pytest.fixture
def vault(tmp_path):
    root = tmp_path / "My Vault"
    _write(root, "Zettel.md", "# Zettel\n\nSee [[Index]] and [[Projects/Alpha|the alpha]].\n")
    _write(root, "README.md", "# Start here\n\nLinks: [[Zettel]], [[Projects/Alpha]].\n")
    _write(root, "Projects/Alpha.md", (
        "---\n"
        "title: Project Alpha\n"
        "tags: [project, active]\n"
        "aliases:\n  - alpha\n"
        "---\n"
        "Decision: ship weekly. Back to [[README#Links]].\n"
        "![[diagram.png|300]]\n"
        "```\n[[not a link]]\n```\n"
    ))
    _write(root, "Projects/index.md", "# Projects\n\n- [[Alpha]]\n- [Zettel](../Zettel.md)\n")
    _write(root, "Projects/beta.txt", "plain text note about beta\n")
    _write(root, "Docs/guide.rst", "Guide\n=====\n\nSome reST text.\n")
    _write(root, "Docs/page.mdx", "---\ntags:\n  - docs\n  - mdx\n---\n# MDX page\n\nbody\n")
    # Never collected: hidden dirs, tool dirs, other file types.
    _write(root, ".obsidian/workspace.md", "# private workspace state\n")
    _write(root, ".trash/old.md", "# deleted note\n")
    _write(root, "node_modules/pkg/README.md", "# dependency readme\n")
    _write(root, ".hidden.md", "# hidden note\n")
    _write(root, "image.png", "not really a png")
    return root


def test_parse_collects_notes_in_folder_order(vault):
    full_text, meta = notes.parse(str(vault))
    assert meta["source_type"] == "notes"
    assert meta["title"] == "My Vault"
    paths = [s["path"] for s in meta["segments"]]
    assert paths == [
        "README.md",
        "Zettel.md",
        "Docs/guide.rst",
        "Docs/page.mdx",
        "Projects/index.md",
        "Projects/Alpha.md",
        "Projects/beta.txt",
    ]
    for seg in meta["segments"]:
        assert seg["key"] == seg["path"]
        assert seg["start_s"] is None and seg["pages"] is None
        assert full_text[seg["offset"]:].startswith(f"=== {seg['title']} ===")
    assert meta["file_count"] == 7
    assert meta["words"] == len(full_text.split())
    assert meta["est_tokens"] > 0
    assert "private workspace" not in full_text
    assert "deleted note" not in full_text
    assert "dependency readme" not in full_text
    assert "hidden note" not in full_text


def test_titles_from_frontmatter_h1_rst_or_filename(vault):
    _, meta = notes.parse(str(vault))
    titles = {s["path"]: s["title"] for s in meta["segments"]}
    assert titles["Projects/Alpha.md"] == "Project Alpha"
    assert titles["README.md"] == "Start here"
    assert titles["Docs/guide.rst"] == "Guide"
    assert titles["Docs/page.mdx"] == "MDX page"
    assert titles["Projects/beta.txt"] == "beta"


def test_frontmatter_stripped_and_tags_kept(vault):
    full_text, meta = notes.parse(str(vault))
    segs = {s["path"]: s for s in meta["segments"]}
    assert segs["Projects/Alpha.md"]["tags"] == ["project", "active"]
    assert segs["Docs/page.mdx"]["tags"] == ["docs", "mdx"]
    assert "tags" not in segs["README.md"]
    assert "title: Project Alpha" not in full_text
    assert "aliases" not in full_text
    assert meta["tags"] == {"active": 1, "docs": 1, "mdx": 1, "project": 1}


def test_wikilinks_become_text_and_are_recorded(vault):
    full_text, meta = notes.parse(str(vault))
    segs = {s["path"]: s for s in meta["segments"]}
    assert "See Index and the alpha." in full_text
    assert "Back to README > Links." in full_text
    assert "[embed: diagram.png]" in full_text
    assert "[[not a link]]" in full_text  # fenced code is left alone
    assert segs["Zettel.md"]["links"] == ["Index", "Projects/Alpha"]
    assert segs["Projects/Alpha.md"]["links"] == ["README"]
    # Relative Markdown links to other notes count as links too.
    assert segs["Projects/index.md"]["links"] == ["Alpha", "Zettel"]
    assert "links" not in segs["Projects/beta.txt"]


def test_hubs_rank_notes_by_inbound_links(vault):
    _, meta = notes.parse(str(vault))
    hubs = {h["path"]: h["inbound"] for h in meta["hubs"]}
    # Alpha: from Zettel, README and Projects/index.
    assert hubs["Projects/Alpha.md"] == 3
    # Zettel: from README and Projects/index (Markdown link).
    assert hubs["Zettel.md"] == 2
    assert meta["hubs"][0]["path"] == "Projects/Alpha.md"


def test_origin_never_contains_the_home_path(vault, monkeypatch):
    monkeypatch.setattr(notes.Path, "home", lambda: vault.parent)
    full_text, meta = notes.parse(str(vault))
    assert meta["origin"] == "~/My Vault"
    assert str(vault.parent) not in full_text
    assert str(vault.parent) not in str(meta)


def test_binary_and_huge_files_are_skipped(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(config, "NOTES_MAX_FILE_BYTES", 100)
    _write(tmp_path, "a.md", "# A\n\nfine\n")
    _write(tmp_path, "huge.md", "x " * 100)
    (tmp_path / "bin.md").write_bytes(b"\x00\x01binary")
    _, meta = notes.parse(str(tmp_path))
    assert [s["path"] for s in meta["segments"]] == ["a.md"]
    err = capsys.readouterr().err
    assert "huge.md" in err and "bin.md" in err


def test_text_cap_drops_later_notes(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(config, "NOTES_TEXT_CAP_BYTES", 50)
    _write(tmp_path, "a.md", "a " * 40)
    _write(tmp_path, "b.md", "b " * 40)
    _, meta = notes.parse(str(tmp_path))
    assert [s["path"] for s in meta["segments"]] == ["a.md"]
    assert "text cap" in capsys.readouterr().err


def test_empty_notes_are_skipped(tmp_path):
    _write(tmp_path, "a.md", "# A\n\ncontent\n")
    _write(tmp_path, "empty.md", "---\ntags: [x]\n---\n\n")
    _, meta = notes.parse(str(tmp_path))
    assert [s["path"] for s in meta["segments"]] == ["a.md"]


def test_symlink_out_of_the_folder_is_not_followed(tmp_path):
    outside = tmp_path / "outside"
    _write(outside, "secret.md", "# secret\n")
    root = tmp_path / "vault"
    _write(root, "a.md", "# A\n\ncontent\n")
    (root / "link.md").symlink_to(outside / "secret.md")
    (root / "dir").symlink_to(outside, target_is_directory=True)
    full_text, meta = notes.parse(str(root))
    assert [s["path"] for s in meta["segments"]] == ["a.md"]
    assert "secret" not in full_text


def test_not_a_directory_fails(tmp_path):
    with pytest.raises(ExtractError, match="not a directory"):
        notes.parse(str(tmp_path / "missing"))


def test_folder_without_notes_fails(tmp_path):
    _write(tmp_path, "pic.png", "x")
    with pytest.raises(ExtractError, match="No notes found"):
        notes.parse(str(tmp_path))


def test_crlf_frontmatter_is_stripped(tmp_path):
    _write(tmp_path, "a.md", "---\r\ntitle: Win note\r\n---\r\nbody text\r\n")
    full_text, meta = notes.parse(str(tmp_path))
    assert meta["segments"][0]["title"] == "Win note"
    assert "title:" not in full_text


def test_leading_horizontal_rule_is_not_frontmatter(tmp_path):
    _write(tmp_path, "a.md", (
        "---\nIntro paragraph that must survive.\n\n## Heading\n---\nrest\n"
    ))
    full_text, _ = notes.parse(str(tmp_path))
    assert "Intro paragraph that must survive." in full_text
    assert "## Heading" in full_text and "rest" in full_text


def test_frontmatter_with_comments_lists_and_continuations(tmp_path):
    _write(tmp_path, "a.md", (
        "---\n# a comment\ntitle: Real\ntags:\n- one\n  - two\n"
        "summary: >\n  folded line\n\naliases: [x]\n---\nbody\n"
    ))
    full_text, meta = notes.parse(str(tmp_path))
    assert meta["segments"][0]["title"] == "Real"
    assert meta["segments"][0]["tags"] == ["one", "two"]
    assert "summary" not in full_text and "body" in full_text


def test_dropped_notes_are_recorded_in_metadata(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "NOTES_TEXT_CAP_BYTES", 50)
    monkeypatch.setattr(config, "NOTES_MAX_FILE_BYTES", 150)
    _write(tmp_path, "a.md", "a " * 40)
    _write(tmp_path, "b.md", "b " * 40)
    _write(tmp_path, "c.md", "c " * 100)
    _, meta = notes.parse(str(tmp_path))
    assert meta["dropped"] == [
        {"path": "b.md", "reason": "over text cap"},
        {"path": "c.md", "reason": "over file size limit"},
    ]


def test_no_dropped_notes_is_an_empty_list(tmp_path):
    _write(tmp_path, "a.md", "# A\n\ncontent\n")
    assert notes.parse(str(tmp_path))[1]["dropped"] == []
