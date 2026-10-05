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
        "ReadMe.txt": "Demo\n\nBody text of the readme.\n",
        "docs/guide.md": GUIDE,
    }
    tar_path = make_tarball(tmp_path, files)
    serve_tarball(monkeypatch, tmp_path, tar_path)
    full_text, meta = repo.parse("https://github.com/octocat/demo")
    titles = [s["title"] for s in meta["segments"]]
    assert titles == ["ReadMe.txt", "User Guide"]
    assert "Body text of the readme." in full_text


def test_parse_reads_rst_and_mdx_docs_with_rst_titles(tmp_path, monkeypatch):
    # Sphinx (Flask, Django, ...) and Docusaurus docs are not Markdown.
    files = {
        "README.rst": "Demo\n====\n\nBody text of the readme.\n",
        "docs/quickstart.rst": (
            ".. _quickstart:\n\n==========\nQuickstart\n==========\n\n"
            "Install it.\n"
        ),
        "docs/no-title.rst": "Just prose, no section title.\n",
        "doc/intro.mdx": "# Intro\n\n<Callout>Hi</Callout>\n",
        "docs/conf.py": "project = 'demo'\n",
    }
    tar_path = make_tarball(tmp_path, files)
    serve_tarball(monkeypatch, tmp_path, tar_path)
    full_text, meta = repo.parse("https://github.com/octocat/demo")
    titles = [s["title"] for s in meta["segments"]]
    assert titles == ["Demo", "Intro", "docs/no-title.rst", "Quickstart"]
    assert "Install it." in full_text
    assert "project = 'demo'" not in full_text


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


# --- Sphinx / MkDocs fidelity ------------------------------------------------


def parse_files(tmp_path, monkeypatch, files, links=None):
    tar_path = make_tarball(tmp_path, files, links=links)
    serve_tarball(monkeypatch, tmp_path, tar_path)
    return repo.parse("https://github.com/octocat/demo")


def segment_text(full_text, meta, path):
    segs = meta["segments"]
    for index, seg in enumerate(segs):
        if seg["path"] == path:
            end = (
                segs[index + 1]["offset"] if index + 1 < len(segs)
                else len(full_text)
            )
            return full_text[seg["offset"]:end]
    raise AssertionError(f"no segment for {path}")


CHANGES_RST = (
    "Version 2.0\n-----------\n\n"
    "Released 2024-01-01\n\n"
    "-   Fixed :issue:`42` in :meth:`Flask.run`. " + "Details. " * 30 + "\n"
)


def test_rst_include_and_literalinclude_are_resolved(tmp_path, monkeypatch):
    files = {
        "README.md": README,
        "CHANGES.rst": CHANGES_RST,
        "LICENSE.txt": "Copyright 2010 Pallets\n\n:meth:`kept` verbatim\n",
        "docs/changes.rst": "Changes\n=======\n\n.. include:: ../CHANGES.rst\n",
        "docs/license.rst": (
            "License\n=======\n\n.. literalinclude:: ../LICENSE.txt\n"
            "    :language: text\n"
        ),
    }
    full_text, meta = parse_files(tmp_path, monkeypatch, files)
    changes = segment_text(full_text, meta, "docs/changes.rst")
    assert ".. include::" not in changes
    assert "Released 2024-01-01" in changes
    # Included reST gets the same markup cleanup.
    assert "Fixed #42 in Flask.run." in changes
    lic = segment_text(full_text, meta, "docs/license.rst")
    assert ".. literalinclude::" not in lic
    assert ":language:" not in lic
    # literalinclude content is code: inserted verbatim.
    assert "Copyright 2010 Pallets" in lic
    assert ":meth:`kept` verbatim" in lic
    segs = {s["path"]: s for s in meta["segments"]}
    assert "stub" not in segs["docs/changes.rst"]


def test_include_honours_start_after_and_end_before(tmp_path, monkeypatch):
    files = {
        "README.md": README,
        "docs/part.rst": "Title\n=====\n\nPREFIX\n.. start\nMIDDLE\n.. end\nSUFFIX\n",
        "docs/main.rst": (
            "Main\n====\n\n.. include:: part.rst\n"
            "   :start-after: .. start\n   :end-before: .. end\n"
        ),
    }
    full_text, meta = parse_files(tmp_path, monkeypatch, files)
    main = segment_text(full_text, meta, "docs/main.rst")
    assert "MIDDLE" in main
    assert "PREFIX" not in main
    assert "SUFFIX" not in main


def test_include_rejects_escapes_and_warns_on_missing(
    tmp_path, monkeypatch, capsys
):
    files = {
        "README.md": README,
        "docs/a.rst": (
            "A\n=\n\n.. include:: ../../../etc/passwd\n\n"
            ".. include:: /etc/hosts\n\n"
            ".. include:: missing.rst\n"
        ),
    }
    full_text, meta = parse_files(tmp_path, monkeypatch, files)
    a = segment_text(full_text, meta, "docs/a.rst")
    assert ".. include:: ../../../etc/passwd" in a
    assert ".. include:: /etc/hosts" in a
    assert ".. include:: missing.rst" in a
    err = capsys.readouterr().err
    assert "missing.rst" in err
    assert "etc/passwd" in err
    assert "/etc/hosts" in err


def test_include_recursion_is_bounded(tmp_path, monkeypatch, capsys):
    files = {
        "README.md": README,
        "docs/a.rst": "A\n=\n\nA-BODY\n\n.. include:: b.rst\n",
        "docs/b.rst": "B-BODY\n\n.. include:: c.rst\n",
        "docs/c.rst": "C-BODY\n\n.. include:: d.rst\n",
        "docs/d.rst": "D-BODY\n\n.. include:: e.rst\n",
        "docs/e.rst": "E-BODY\n",
        "docs/loop.rst": "Loop\n====\n\nLOOP-BODY\n\n.. include:: loop.rst\n",
    }
    full_text, meta = parse_files(tmp_path, monkeypatch, files)
    a = segment_text(full_text, meta, "docs/a.rst")
    assert "D-BODY" in a
    assert "E-BODY" not in a
    assert ".. include:: e.rst" in a
    loop = segment_text(full_text, meta, "docs/loop.rst")
    assert loop.count("LOOP-BODY") == 1
    assert "e.rst" in capsys.readouterr().err


def test_include_respects_text_cap(tmp_path, monkeypatch, capsys):
    files = {
        "README.md": README,
        "docs/big.txt": "x" * 500,
        "docs/a.rst": "A\n=\n\n.. literalinclude:: big.txt\n",
    }
    tar_path = make_tarball(tmp_path, files)
    serve_tarball(monkeypatch, tmp_path, tar_path)
    monkeypatch.setattr(repo.config, "REPO_TEXT_CAP_BYTES", 300)
    full_text, meta = repo.parse("https://github.com/octocat/demo")
    assert "x" * 500 not in full_text
    assert "big.txt" in capsys.readouterr().err


def test_myst_include_fence_is_resolved(tmp_path, monkeypatch):
    files = {
        "README.md": README,
        "CHANGELOG.md": "# Changelog\n\n## 1.0\n\nShipped it.\n",
        "docs/changelog.md": "```{include} ../CHANGELOG.md\n```\n",
        "docs/guide.md": "# Guide\n\n```python\n```{include} not-a-directive\n```\n",
    }
    full_text, meta = parse_files(tmp_path, monkeypatch, files)
    log = segment_text(full_text, meta, "docs/changelog.md")
    assert "Shipped it." in log
    assert "{include}" not in log
    # The top-level CHANGELOG.md is now covered by the docs page.
    assert [s["path"] for s in meta["segments"]] == [
        "README.md", "docs/changelog.md", "docs/guide.md",
    ]
    assert meta["segments"][1]["title"] == "Changelog"


def test_rst_roles_reduce_to_readable_text(tmp_path, monkeypatch):
    doc = (
        "Roles\n=====\n\n"
        "Call :meth:`Flask.run` on :class:`~flask.Flask` with :data:`x`.\n"
        "See :ref:`the guide <guide-label>` and :doc:`/tutorial/index`.\n"
        "Also :py:func:`.url_for`, :pep:`8`, :issue:`12` and :gh:`ex <a/b>`.\n"
    )
    full_text, meta = parse_files(
        tmp_path, monkeypatch, {"README.md": README, "docs/r.rst": doc}
    )
    body = segment_text(full_text, meta, "docs/r.rst")
    assert "Call Flask.run on Flask with x." in body
    assert "See the guide and /tutorial/index." in body
    assert "Also url_for, PEP 8, #12 and ex." in body
    assert ":meth:" not in body


def test_rst_code_blocks_are_kept_verbatim(tmp_path, monkeypatch):
    doc = (
        "Code\n====\n\n"
        "Example::\n\n"
        "    x = ':meth:`raw`'\n"
        "    .. note:: inside literal\n\n"
        ".. code-block:: python\n"
        "    :caption: app.py\n"
        "    :linenos:\n\n"
        "    @app.route(':class:`y`')\n"
        "    def index(): ...\n\n"
        "After :class:`Z`.\n"
    )
    full_text, meta = parse_files(
        tmp_path, monkeypatch, {"README.md": README, "docs/c.rst": doc}
    )
    body = segment_text(full_text, meta, "docs/c.rst")
    assert "    x = ':meth:`raw`'\n" in body
    assert "    .. note:: inside literal\n" in body
    assert "    @app.route(':class:`y`')\n    def index(): ...\n" in body
    assert ".. code-block:: python" in body
    assert ":caption:" not in body
    assert ":linenos:" not in body
    assert "After Z." in body


def test_rst_directives_become_short_readable_lines(tmp_path, monkeypatch):
    doc = (
        ".. _label:\n\n"
        "Dirs\n====\n\n"
        ".. currentmodule:: flask\n\n"
        ".. autoclass:: Flask\n"
        "   :members:\n"
        "   :inherited-members:\n\n"
        ".. automodule:: flask.json\n\n"
        ".. autofunction:: flask.ctx.after_this_request\n\n"
        ".. versionadded:: 2.0\n\n"
        ".. versionchanged:: 2.3\n"
        "    Not set by default.\n\n"
        ".. deprecated:: 2.2\n"
        "    Will be removed.\n\n"
        ".. note::\n\n"
        "    Be careful with :class:`X`.\n\n"
        ".. warning:: Hot.\n\n"
        ".. admonition:: Errors in Scripts\n\n"
        "    Body.\n\n"
        ".. image:: _static/logo.svg\n"
        "    :align: center\n\n"
        ".. This is a comment\n"
        "   spanning lines.\n\n"
        ".. _Werkzeug: https://werkzeug.example\n"
    )
    full_text, meta = parse_files(
        tmp_path, monkeypatch, {"README.md": README, "docs/d.rst": doc}
    )
    body = segment_text(full_text, meta, "docs/d.rst")
    assert "API reference: flask.Flask (autodoc, see source)" in body
    assert "API reference: flask.json (autodoc, see source)" in body
    assert (
        "API reference: flask.ctx.after_this_request (autodoc, see source)"
        in body
    )
    assert ":members:" not in body
    assert "Added in version 2.0." in body
    assert "Changed in version 2.3." in body
    assert "Not set by default." in body
    assert "Deprecated since version 2.2." in body
    assert "Note:" in body
    assert "Be careful with X." in body
    assert "Warning: Hot." in body
    assert "Errors in Scripts:" in body
    assert "logo.svg" not in body
    assert "This is a comment" not in body
    assert "spanning lines" not in body
    assert ".. _label:" not in body
    assert "currentmodule" not in body
    assert "https://werkzeug.example" in body
    assert meta["segments"][1]["title"] == "Dirs"


def test_sphinx_toctree_sets_reading_order(tmp_path, monkeypatch):
    files = {
        "README.rst": "Demo\n====\n\nReadme.\n",
        "docs/index.rst": (
            "Welcome\n=======\n\n"
            ".. toctree::\n   :maxdepth: 2\n\n"
            "   quickstart\n   tutorial/index\n   Changes <changes>\n"
            "   self\n   glob/*\n   https://example.com\n"
        ),
        "docs/quickstart.rst": "Quickstart\n==========\n\nQ.\n",
        "docs/tutorial/index.rst": (
            "Tutorial\n========\n\n.. toctree::\n   :caption: Steps\n\n"
            "   setup\n   /api\n"
        ),
        "docs/tutorial/setup.rst": "Setup\n=====\n\nS.\n",
        "docs/api.rst": "API\n===\n\nA.\n",
        "docs/changes.rst": "Changes\n=======\n\nC.\n",
        "docs/aaa-unlisted.rst": "Unlisted\n========\n\nU.\n",
    }
    full_text, meta = parse_files(tmp_path, monkeypatch, files)
    assert [s["path"] for s in meta["segments"]] == [
        "README.rst",
        "docs/index.rst",
        "docs/quickstart.rst",
        "docs/tutorial/index.rst",
        "docs/tutorial/setup.rst",
        "docs/api.rst",
        "docs/changes.rst",
        "docs/aaa-unlisted.rst",
    ]
    index = segment_text(full_text, meta, "docs/index.rst")
    assert "toctree" not in index
    assert "quickstart" not in index
    offsets = [s["offset"] for s in meta["segments"]]
    assert offsets == sorted(offsets)
    for seg in meta["segments"]:
        assert full_text[seg["offset"]:].startswith(f"=== {seg['title']} ===\n")


def test_mkdocs_nav_sets_reading_order(tmp_path, monkeypatch):
    files = {
        "README.md": README,
        "mkdocs.yml": (
            "site_name: Demo\n"
            "theme:\n  name: material\n"
            "nav:\n"
            "    - Introduction: 'index.md'\n"
            "    - QuickStart: quickstart.md\n"
            "    - Advanced:\n"
            "        - Clients: 'advanced/clients.md'\n"
            "        - \"Auth: basics\": \"advanced/auth.md\"\n"
            "    - Source: https://github.com/octocat/demo\n"
            "markdown_extensions:\n  - admonition\n"
        ),
        "docs/advanced/auth.md": "# Auth\n\nA.\n",
        "docs/advanced/clients.md": "# Clients\n\nC.\n",
        "docs/index.md": "# Intro\n\nI.\n",
        "docs/quickstart.md": "# Quick\n\nQ.\n",
        "docs/zz-extra.md": "# Extra\n\nE.\n",
        "docs/aa-extra.md": "# AExtra\n\nE.\n",
    }
    _, meta = parse_files(tmp_path, monkeypatch, files)
    assert [s["path"] for s in meta["segments"]] == [
        "README.md",
        "docs/index.md",
        "docs/quickstart.md",
        "docs/advanced/clients.md",
        "docs/advanced/auth.md",
        "docs/aa-extra.md",
        "docs/zz-extra.md",
    ]


def test_mkdocs_unparseable_nav_falls_back_to_filename_order(
    tmp_path, monkeypatch, capsys
):
    files = {
        "README.md": README,
        "mkdocs.yml": "nav: !!python/object:evil {}\n\tbroken: [\n",
        "docs/b.md": "# B\n",
        "docs/a.md": "# A\n",
    }
    _, meta = parse_files(tmp_path, monkeypatch, files)
    assert [s["path"] for s in meta["segments"]] == [
        "README.md", "docs/a.md", "docs/b.md",
    ]
    assert capsys.readouterr().err == ""


def test_orphan_and_stub_segments_are_flagged_not_dropped(
    tmp_path, monkeypatch
):
    long_body = "Real content sentence. " * 20
    files = {
        "README.md": "# Demo\n\n" + long_body,
        "docs/orphan.rst": ":orphan:\n\nOrphan\n======\n\n" + long_body,
        "docs/stub.rst": "Stub\n====\n\nMoved elsewhere.\n",
        "docs/full.md": "# Full\n\n" + long_body,
    }
    full_text, meta = parse_files(tmp_path, monkeypatch, files)
    segs = {s["path"]: s for s in meta["segments"]}
    assert segs["docs/orphan.rst"].get("orphan") is True
    assert "stub" not in segs["docs/orphan.rst"]
    assert segs["docs/orphan.rst"]["title"] == "Orphan"
    assert ":orphan:" not in segment_text(full_text, meta, "docs/orphan.rst")
    assert segs["docs/stub.rst"].get("stub") is True
    assert "orphan" not in segs["docs/stub.rst"]
    assert "orphan" not in segs["docs/full.md"]
    assert "stub" not in segs["docs/full.md"]
    assert "stub" not in segs["README.md"]


def test_rst_roles_spanning_lines_and_in_footnotes(tmp_path, monkeypatch):
    doc = (
        "Wrap\n====\n\n"
        ":gh:`The tutorial project is in the\n"
        "repository <examples/tutorial>`, compare it.\n\n"
        ".. [#] What is :class:`~flask.g`?\n"
    )
    full_text, meta = parse_files(
        tmp_path, monkeypatch, {"README.md": README, "docs/w.rst": doc}
    )
    body = segment_text(full_text, meta, "docs/w.rst")
    assert "The tutorial project is in the repository, compare it." in body
    assert ".. [#] What is g?" in body
    assert ":gh:" not in body
