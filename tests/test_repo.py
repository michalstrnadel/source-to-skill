import io
import tarfile
import urllib.error

import pytest

from extractor.parsers import repo
from extractor.utils import ExtractError

README = "# Demo Project\n\nA tool that does things.\n"
CHANGELOG = "## 0.1.0\n\nFirst release.\n"
CONTRIBUTING = "# Contributing\n\nSend patches.\n"
GUIDE = "# User Guide\n\nRun the tool with care.\n"
REFERENCE = "API reference body without any heading.\n"
LICENSE_MD = "# MIT License\n\nDo anything.\n"

FILES = {
    "README.md": README,
    "CHANGELOG.md": CHANGELOG,
    "CONTRIBUTING.md": CONTRIBUTING,
    "LICENSE.md": LICENSE_MD,
    "src/main.py": "print('hi')\n",
    "docs/guide.md": GUIDE,
    "docs/api/reference.md": REFERENCE,
}


def make_tarball(tmp_path, files, root="demo-HEAD", name="src.tar.gz",
                 links=None):
    """Build a codeload-style tarball; keys starting with / stay absolute."""
    path = tmp_path / name
    with tarfile.open(path, "w:gz") as tf:
        for rel, text in files.items():
            data = text.encode("utf-8")
            member = rel if rel.startswith("/") else f"{root}/{rel}"
            info = tarfile.TarInfo(member)
            info.size = len(data)
            tf.addfile(info, io.BytesIO(data))
        for rel, target in (links or {}).items():
            info = tarfile.TarInfo(f"{root}/{rel}")
            info.type = tarfile.SYMTYPE
            info.linkname = target
            tf.addfile(info)
    return path


def serve_tarball(monkeypatch, tmp_path, tar_path):
    """Mock urlopen to serve `tar_path`; return the recorded calls."""
    calls = {}

    def fake_urlopen(url, timeout=None):
        calls["url"] = url
        calls["timeout"] = timeout
        return open(tar_path, "rb")

    monkeypatch.setattr(repo.config, "work_dir", lambda: tmp_path / "work")
    monkeypatch.setattr(repo.urllib.request, "urlopen", fake_urlopen)
    return calls


def test_parse_reads_readme_top_level_md_and_docs(tmp_path, monkeypatch):
    tar_path = make_tarball(tmp_path, FILES)
    calls = serve_tarball(monkeypatch, tmp_path, tar_path)
    full_text, meta = repo.parse("https://github.com/octocat/demo")
    assert calls["url"] == "https://codeload.github.com/octocat/demo/tar.gz/HEAD"
    assert calls["timeout"] == repo.config.FETCH_TIMEOUT_S
    assert meta["source_type"] == "repo"
    assert meta["title"] == "octocat/demo"
    assert meta["owner"] == "octocat"
    assert meta["repo"] == "demo"
    assert meta["origin"] == "https://github.com/octocat/demo"
    assert meta["file_count"] == 5
    assert meta["words"] == len(full_text.split())
    assert meta["est_tokens"] > 0
    titles = [s["title"] for s in meta["segments"]]
    assert titles == [
        "Demo Project",
        "CHANGELOG.md",
        "Contributing",
        "docs/api/reference.md",
        "User Guide",
    ]
    assert all(s["start_s"] is None for s in meta["segments"])
    assert all(s["pages"] is None for s in meta["segments"])
    offsets = [s["offset"] for s in meta["segments"]]
    assert offsets[0] == 0
    assert offsets == sorted(offsets)
    assert len(set(offsets)) == len(offsets)
    for seg in meta["segments"]:
        chunk_head = full_text[seg["offset"]:].splitlines()[0]
        assert chunk_head == f"=== {seg['title']} ==="
    assert "A tool that does things." in full_text
    assert "Run the tool with care." in full_text
    assert "Do anything." not in full_text
    assert "print('hi')" not in full_text


def test_parse_accepts_any_case_readme_and_falls_back_to_path_title(
    tmp_path, monkeypatch
):
    files = {
        "ReadMe.rst": "Demo\n====\n\nBody text of the readme.\n",
        "docs/guide.md": GUIDE,
    }
    tar_path = make_tarball(tmp_path, files)
    serve_tarball(monkeypatch, tmp_path, tar_path)
    full_text, meta = repo.parse("https://github.com/octocat/demo")
    titles = [s["title"] for s in meta["segments"]]
    assert titles == ["ReadMe.rst", "User Guide"]
    assert "Body text of the readme." in full_text


def test_parse_normalizes_dot_git_and_trailing_slash(tmp_path, monkeypatch):
    tar_path = make_tarball(tmp_path, {"README.md": README})
    calls = serve_tarball(monkeypatch, tmp_path, tar_path)
    _, meta = repo.parse("https://github.com/octocat/demo.git")
    assert calls["url"] == "https://codeload.github.com/octocat/demo/tar.gz/HEAD"
    assert meta["repo"] == "demo"
    _, meta = repo.parse("https://github.com/octocat/demo/")
    assert meta["repo"] == "demo"


def test_parse_accepts_readme_tab_query_and_fragment(tmp_path, monkeypatch):
    # GitHub's own UI appends ?tab=readme-ov-file / #readme to repo URLs.
    tar_path = make_tarball(tmp_path, {"README.md": README})
    calls = serve_tarball(monkeypatch, tmp_path, tar_path)
    _, meta = repo.parse("https://github.com/octocat/demo?tab=readme-ov-file")
    assert calls["url"] == "https://codeload.github.com/octocat/demo/tar.gz/HEAD"
    assert meta["repo"] == "demo"
    _, meta = repo.parse("https://github.com/octocat/demo#readme")
    assert meta["repo"] == "demo"
    _, meta = repo.parse("https://GitHub.com/octocat/demo")
    assert meta["repo"] == "demo"


def test_title_ignores_h1_like_comments_inside_code_fences(
    tmp_path, monkeypatch
):
    readme = (
        "[![badge](x)](y)\n\n"
        "```bash\n# install dependencies first\npip install demo\n```\n\n"
        "# Demo Project\n\nBody.\n"
    )
    guide = "~~~\n# fenced comment only\n~~~\n\nNo heading in this file.\n"
    tar_path = make_tarball(
        tmp_path, {"README.md": readme, "docs/guide.md": guide}
    )
    serve_tarball(monkeypatch, tmp_path, tar_path)
    _, meta = repo.parse("https://github.com/octocat/demo")
    titles = [s["title"] for s in meta["segments"]]
    assert titles == ["Demo Project", "docs/guide.md"]


def test_parse_follows_in_tree_readme_symlink(tmp_path, monkeypatch):
    # Real repos symlink README.md to a docs source file; an in-tree
    # symlink must not turn the repo into "has no README or docs".
    files = {"docs-src/index.md": "# Linked Guide\n\nSymlinked readme body.\n"}
    tar_path = make_tarball(
        tmp_path, files, links={"README.md": "docs-src/index.md"}
    )
    serve_tarball(monkeypatch, tmp_path, tar_path)
    full_text, meta = repo.parse("https://github.com/octocat/demo")
    assert [s["title"] for s in meta["segments"]] == ["Linked Guide"]
    assert "Symlinked readme body." in full_text


def test_parse_follows_in_tree_symlink_without_data_filter(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(repo, "tarfile", _TarfileWithoutDataFilter())
    files = {"docs-src/index.md": "# Linked Guide\n\nSymlinked readme body.\n"}
    tar_path = make_tarball(
        tmp_path, files, links={"README.md": "docs-src/index.md"}
    )
    serve_tarball(monkeypatch, tmp_path, tar_path)
    _, meta = repo.parse("https://github.com/octocat/demo")
    assert [s["title"] for s in meta["segments"]] == ["Linked Guide"]


def test_parse_still_skips_out_of_tree_symlink(tmp_path, monkeypatch, capsys):
    tar_path = make_tarball(
        tmp_path, {"README.md": README}, links={"evil.md": "../../outside.md"}
    )
    serve_tarball(monkeypatch, tmp_path, tar_path)
    _, meta = repo.parse("https://github.com/octocat/demo")
    assert [s["title"] for s in meta["segments"]] == ["Demo Project"]
    assert "evil.md" in capsys.readouterr().err


def test_parse_rejects_path_traversal_members(tmp_path, monkeypatch, capsys):
    files = {
        "README.md": README,
        "../../escape.md": "# Escaped\n",
        "/abs-escape.md": "# Absolute\n",
    }
    tar_path = make_tarball(tmp_path, files)
    serve_tarball(monkeypatch, tmp_path, tar_path)
    full_text, meta = repo.parse("https://github.com/octocat/demo")
    assert [s["title"] for s in meta["segments"]] == ["Demo Project"]
    err = capsys.readouterr().err
    assert "escape.md" in err
    assert "abs-escape.md" in err
    assert not list(tmp_path.rglob("escape.md"))
    assert not list(tmp_path.rglob("abs-escape.md"))
    assert "Escaped" not in full_text
    assert "Absolute" not in full_text


class _TarfileWithoutDataFilter:
    """Proxy for the tarfile module as seen on Python 3.10/3.11."""

    def __getattr__(self, name):
        if name == "data_filter":
            raise AttributeError(name)
        return getattr(tarfile, name)


def test_parse_traversal_rejected_without_data_filter(
    tmp_path, monkeypatch, capsys
):
    # Simulate Python 3.10/3.11: no tarfile.data_filter, so the manual
    # member sanitization fallback must reject the traversal member.
    monkeypatch.setattr(repo, "tarfile", _TarfileWithoutDataFilter())
    files = {"README.md": README, "../../escape.md": "# Escaped\n"}
    tar_path = make_tarball(tmp_path, files)
    serve_tarball(monkeypatch, tmp_path, tar_path)
    _, meta = repo.parse("https://github.com/octocat/demo")
    assert [s["title"] for s in meta["segments"]] == ["Demo Project"]
    assert "escape.md" in capsys.readouterr().err
    assert not list(tmp_path.rglob("escape.md"))


def test_member_is_safe_rejects_unsafe_members():
    assert repo._member_is_safe(tarfile.TarInfo("demo-HEAD/README.md"))
    docs_dir = tarfile.TarInfo("demo-HEAD/docs")
    docs_dir.type = tarfile.DIRTYPE
    assert repo._member_is_safe(docs_dir)
    for name in (
        "/etc/passwd",
        "demo-HEAD/../../escape.md",
        "..\\escape.md",
        "C:\\escape.md",
    ):
        assert not repo._member_is_safe(tarfile.TarInfo(name))
    link = tarfile.TarInfo("demo-HEAD/link.md")
    link.type = tarfile.SYMTYPE
    link.linkname = "../../secret"
    assert not repo._member_is_safe(link)
    abs_link = tarfile.TarInfo("demo-HEAD/link.md")
    abs_link.type = tarfile.SYMTYPE
    abs_link.linkname = "/etc/passwd"
    assert not repo._member_is_safe(abs_link)
    in_tree_link = tarfile.TarInfo("demo-HEAD/README.md")
    in_tree_link.type = tarfile.SYMTYPE
    in_tree_link.linkname = "docs/index.md"
    assert repo._member_is_safe(in_tree_link)
    dev = tarfile.TarInfo("demo-HEAD/dev")
    dev.type = tarfile.CHRTYPE
    assert not repo._member_is_safe(dev)


def test_parse_caps_total_text_and_warns(tmp_path, monkeypatch, capsys):
    files = {
        "README.md": README,
        "docs/big.md": "# Big\n" + "word " * 200,
        "docs/tiny.md": "# Tiny\nfits\n",
    }
    tar_path = make_tarball(tmp_path, files)
    serve_tarball(monkeypatch, tmp_path, tar_path)
    cap = len(README.encode("utf-8")) + 40
    monkeypatch.setattr(repo.config, "REPO_TEXT_CAP_BYTES", cap)
    full_text, meta = repo.parse("https://github.com/octocat/demo")
    titles = [s["title"] for s in meta["segments"]]
    assert titles == ["Demo Project", "Tiny"]
    assert meta["file_count"] == 2
    assert "word word" not in full_text
    err = capsys.readouterr().err
    assert "docs/big.md" in err
    assert "cap" in err.lower()


def test_parse_first_file_kept_even_over_cap(tmp_path, monkeypatch):
    tar_path = make_tarball(tmp_path, {"README.md": README})
    serve_tarball(monkeypatch, tmp_path, tar_path)
    monkeypatch.setattr(repo.config, "REPO_TEXT_CAP_BYTES", 5)
    full_text, meta = repo.parse("https://github.com/octocat/demo")
    assert [s["title"] for s in meta["segments"]] == ["Demo Project"]
    assert "A tool that does things." in full_text


def test_parse_without_readme_or_docs_errors(tmp_path, monkeypatch):
    files = {
        "src/main.py": "print('hi')\n",
        "LICENSE.md": LICENSE_MD,
        "notes.txt": "misc notes\n",
    }
    tar_path = make_tarball(tmp_path, files)
    serve_tarball(monkeypatch, tmp_path, tar_path)
    with pytest.raises(ExtractError, match="README"):
        repo.parse("https://github.com/octocat/demo")


def test_parse_missing_repo_404_errors(tmp_path, monkeypatch):
    def fake_urlopen(url, timeout=None):
        raise urllib.error.HTTPError(url, 404, "Not Found", None, None)

    monkeypatch.setattr(repo.config, "work_dir", lambda: tmp_path / "work")
    monkeypatch.setattr(repo.urllib.request, "urlopen", fake_urlopen)
    with pytest.raises(ExtractError, match="private"):
        repo.parse("https://github.com/octocat/ghost")


def test_parse_network_error_suggests_retry(tmp_path, monkeypatch):
    def fake_urlopen(url, timeout=None):
        raise urllib.error.URLError("dns resolution failed")

    monkeypatch.setattr(repo.config, "work_dir", lambda: tmp_path / "work")
    monkeypatch.setattr(repo.urllib.request, "urlopen", fake_urlopen)
    with pytest.raises(ExtractError, match="network"):
        repo.parse("https://github.com/octocat/demo")


def test_parse_stalled_download_timeout_errors(tmp_path, monkeypatch):
    def fake_urlopen(url, timeout=None):
        raise TimeoutError("timed out")

    monkeypatch.setattr(repo.config, "work_dir", lambda: tmp_path / "work")
    monkeypatch.setattr(repo.urllib.request, "urlopen", fake_urlopen)
    with pytest.raises(ExtractError, match="network"):
        repo.parse("https://github.com/octocat/demo")


def test_parse_rejects_non_repo_url():
    with pytest.raises(ExtractError, match="GitHub"):
        repo.parse("https://github.com/octocat/demo/tree/main")
