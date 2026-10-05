"""GitHub repo parser: codeload tarball + README and docs extraction."""
import posixpath
import re
import shutil
import sys
import tarfile
import urllib.error
import urllib.request
from pathlib import Path

from .. import config, utils
from ..utils import ExtractError

# Query/fragment tails (?tab=readme-ov-file, #readme) are fine; GitHub's
# own UI appends them to bare repo URLs.
REPO_URL_RE = re.compile(
    r"(?:https?://)?(?:www\.)?github\.com/"
    r"(?P<owner>[A-Za-z0-9][A-Za-z0-9-]*)/(?P<repo>[A-Za-z0-9._-]+?)"
    r"/?(?:[?#].*)?$",
    re.IGNORECASE,
)
TARBALL_URL = "https://codeload.github.com/{owner}/{repo}/tar.gz/HEAD"

README_SUFFIXES = (".md", ".rst", ".txt")
# Docs-folder formats: Markdown, MDX (Docusaurus, Nextra) and
# reStructuredText (Sphinx - most Python projects).
DOC_SUFFIXES = (".md", ".mdx", ".rst")
DOC_DIRS = ("docs", "doc")
H1_RE = re.compile(r"^#[ \t]+(.+?)\s*$")
# reST section underline/overline: one punctuation char repeated.
RST_RULE_RE = re.compile(r"^([=\-~^\"'`#*+:.])\1{2,}\s*$")
FENCE_PREFIXES = ("```", "~~~")


def _warn(message: str) -> None:
    print(f"WARNING: {message}", file=sys.stderr)


def _download(owner: str, repo_name: str) -> Path:
    tarball_url = TARBALL_URL.format(owner=owner, repo=repo_name)
    target = config.work_dir() / f"repo-{owner}-{repo_name}.tar.gz"
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        with urllib.request.urlopen(
            tarball_url, timeout=config.FETCH_TIMEOUT_S
        ) as response, open(target, "wb") as tar_file:
            shutil.copyfileobj(response, tar_file)
    except urllib.error.HTTPError as err:
        if err.code == 404:
            raise ExtractError(
                f"GitHub returned 404 for {owner}/{repo_name}.\n"
                "The repository does not exist or is private - check the "
                "URL; private repos are not supported."
            ) from err
        raise ExtractError(
            f"GitHub returned HTTP {err.code} for {tarball_url}.\n"
            "Retry later; if it persists, check the repository URL."
        ) from err
    except (urllib.error.URLError, OSError) as err:
        raise ExtractError(
            f"Cannot download {tarball_url}: {getattr(err, 'reason', err)}\n"
            "Check your network connection and retry."
        ) from err
    return target


def _member_is_safe(member: tarfile.TarInfo) -> bool:
    """Reject absolute paths, `..` escapes, unsafe links, special files.

    In-tree relative symlinks are kept (real repos symlink README.md to a
    docs source file); anything pointing outside the tree is dropped.
    Applied on every Python; on 3.12+ tarfile.data_filter runs on top
    (data_filter alone only strips leading slashes instead of rejecting
    absolute members).
    """
    if not (member.isfile() or member.isdir() or member.issym()):
        return False
    name = member.name.replace("\\", "/")
    if name.startswith("/") or re.match(r"^[A-Za-z]:", name):
        return False
    if ".." in name.split("/"):
        return False
    if member.issym():
        link = member.linkname.replace("\\", "/")
        if link.startswith("/") or re.match(r"^[A-Za-z]:", link):
            return False
        target = posixpath.normpath(
            posixpath.join(posixpath.dirname(name), link)
        )
        if target == ".." or target.startswith("../"):
            return False
    return True


def _skip_unsafe(member, dest_path):
    """tarfile extraction filter: sanitize, then let data_filter re-check."""
    if not _member_is_safe(member):
        _warn(f"skipped unsafe tar member: {member.name}")
        return None
    try:
        return tarfile.data_filter(member, dest_path)
    except tarfile.FilterError:
        _warn(f"skipped unsafe tar member: {member.name}")
        return None


def _extract(tar_path: Path, dest: Path) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    try:
        tf = tarfile.open(tar_path, "r:gz")
    except tarfile.TarError as err:
        raise ExtractError(
            f"{tar_path} is not a valid tarball ({err}).\n"
            "The download may be corrupted - retry."
        ) from err
    with tf:
        if hasattr(tarfile, "data_filter"):
            tf.extractall(dest, filter=_skip_unsafe)
        else:
            members = []
            for member in tf.getmembers():
                if _member_is_safe(member):
                    members.append(member)
                else:
                    _warn(f"skipped unsafe tar member: {member.name}")
            tf.extractall(dest, members=members)


def _repo_root(dest: Path) -> Path:
    """Codeload tarballs wrap everything in a single `<repo>-<ref>/` dir."""
    entries = list(dest.iterdir())
    if len(entries) == 1 and entries[0].is_dir():
        return entries[0]
    return dest


def _select_files(root: Path) -> list[Path]:
    """Doc files in reading order: root README*, top-level *.md, docs/."""
    readmes = []
    top_md = []
    for path in sorted(root.iterdir(), key=lambda p: p.name.lower()):
        if not path.is_file():
            continue
        name = path.name.lower()
        if name.startswith("readme") and path.suffix.lower() in README_SUFFIXES:
            readmes.append(path)
        elif path.suffix.lower() == ".md" and not name.startswith("license"):
            top_md.append(path)
    docs_md = []
    for dir_name in DOC_DIRS:
        docs_dir = root / dir_name
        if docs_dir.is_dir():
            docs_md.extend(
                path
                for path in docs_dir.rglob("*")
                if path.is_file() and path.suffix.lower() in DOC_SUFFIXES
            )
    docs_md.sort(key=lambda p: p.relative_to(root).as_posix().lower())
    return readmes + top_md + _order_docs(root, docs_md)


def _rst_title(text: str):
    """First reST section title (a text line with a rule under it), or None."""
    lines = text.splitlines()
    for index in range(len(lines) - 1):
        title = lines[index].strip()
        if (
            title
            and not RST_RULE_RE.match(title)
            and not title.startswith("..")
            and RST_RULE_RE.match(lines[index + 1].strip())
            and len(lines[index + 1].strip()) >= len(title)
        ):
            return " ".join(title.split())
    return None


def _title(text: str, rel_path: str) -> str:
    """First markdown H1 outside fenced code blocks, else the file path.

    reStructuredText files use their first section title instead.

    Shell comments inside ``` / ~~~ fences look exactly like H1 lines,
    so fenced regions are skipped instead of regex-searching the raw text.
    """
    if rel_path.lower().endswith(".rst"):
        return _rst_title(text) or rel_path
    fence = None
    for line in text.splitlines():
        stripped = line.lstrip()
        if fence is not None:
            if stripped.startswith(fence):
                fence = None
            continue
        if stripped.startswith(FENCE_PREFIXES):
            fence = stripped[:3]
            continue
        match = H1_RE.match(line)
        if match:
            title = " ".join(match.group(1).split())
            if title:
                return title
    return rel_path


# --- Doc rendering: includes, reST markup cleanup ---------------------------

# Nested include depth: a file may include one that includes one that
# includes one, no deeper (cycles are rejected outright).
INCLUDE_MAX_DEPTH = 3
# Segments whose rendered body is shorter than this are flagged `stub`.
STUB_CHARS = 200

DIRECTIVE_RE = re.compile(
    r"^(?P<pad>[ \t]*)\.\.[ \t]+(?P<name>[A-Za-z][\w:.+-]*)::"
    r"(?:[ \t]+(?P<arg>.*?))?\s*$"
)
# Directive option line: `:name: value`. A role (`:meth:`x``) has a
# backtick after the colon, so it never matches.
OPTION_RE = re.compile(r"^[ \t]+:(?P<key>[\w.+-][^:`]*):(?:[ \t]+(?P<val>.*?))?\s*$")
COMMENT_RE = re.compile(r"^(?P<pad>[ \t]*)\.\.(?:[ \t]+(?P<rest>.*))?$")
ROLE_RE = re.compile(
    r":(?P<role>(?:[A-Za-z][\w+-]*:)*[A-Za-z][\w+-]*):`(?P<body>[^`]+)`"
)
# A role opened but not closed on this line (wrapped onto the next one).
ROLE_OPEN_RE = re.compile(r":(?:[A-Za-z][\w+-]*:)*[A-Za-z][\w+-]*:`[^`]*$")
EXPLICIT_TITLE_RE = re.compile(r"^(?P<title>.*?)\s*<(?P<target>[^<>]+)>$", re.S)
FIELD_RE = re.compile(r"^:[\w-]+:(?:\s.*)?$")
MYST_INCLUDE_RE = re.compile(
    r"^(?P<pad>[ \t]*)(?P<fence>`{3,}|~{3,})"
    r"\{(?P<name>include|literalinclude)\}[ \t]+(?P<arg>\S.*?)\s*$"
)

ADMONITIONS = {
    "note": "Note", "warning": "Warning", "tip": "Tip",
    "important": "Important", "caution": "Caution", "attention": "Attention",
    "danger": "Danger", "error": "Error", "hint": "Hint",
    "seealso": "See also", "todo": "Todo",
}
VERSION_DIRECTIVES = {
    "versionadded": "Added in version {}.",
    "versionchanged": "Changed in version {}.",
    "deprecated": "Deprecated since version {}.",
    "versionremoved": "Removed in version {}.",
}
AUTODOC_DIRECTIVES = {
    "autoclass", "automodule", "autofunction", "autodata", "automethod",
    "autoattribute", "autoexception", "autodecorator", "autoproperty",
}
# Content is code/math: kept byte for byte.
CODE_DIRECTIVES = {
    "code-block", "sourcecode", "code", "doctest", "testcode",
    "testoutput", "productionlist", "math", "parsed-literal",
}
# Pure navigation/presentation: directive, options and content dropped.
DROP_DIRECTIVES = {
    "toctree", "image", "raw", "rst-class", "highlight", "index", "meta",
    "contents", "tabularcolumns", "sectionauthor", "moduleauthor",
    "codeauthor", "currentmodule", "module", "default-role",
    "default-domain", "role",
}
# Directive line dropped, content kept.
UNWRAP_DIRECTIVES = {"tabs", "figure", "only", "container", "rubric"}
DOMAIN_OBJECTS = {
    "function", "class", "method", "attribute", "data", "exception",
    "decorator", "envvar", "confval", "option", "describe", "object",
    "property", "classmethod", "staticmethod",
}


class _IncludeCtx:
    """Per-segment include state: repo root, byte budget, files inserted."""

    def __init__(self, root: Path, budget: int):
        self.root = root.resolve()
        self.budget = budget
        self.inserted: set[Path] = set()


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip())


def _role_text(match) -> str:
    role = match.group("role").rsplit(":", 1)[-1].lower()
    body = match.group("body").strip()
    explicit = EXPLICIT_TITLE_RE.match(body)
    if explicit and explicit.group("title"):
        return explicit.group("title")
    text = body.lstrip("!")
    if text.startswith("~"):
        text = text[1:].strip(".").rsplit(".", 1)[-1]
    else:
        text = text.lstrip(".")
    if role == "pep":
        return f"PEP {text}"
    if role == "rfc":
        return f"RFC {text}"
    if role in ("issue", "pr") and text.isdigit():
        return f"#{text}"
    return text


def _simplify_roles(line: str) -> str:
    return ROLE_RE.sub(_role_text, line)


def _slice_include(text: str, opts: dict, label: str) -> str:
    """Apply :start-line:/:end-line:/:start-after:/:end-before:."""
    lines_opt = [opts.get("start-line"), opts.get("end-line")]
    if any(v is not None for v in lines_opt):
        try:
            start = int(lines_opt[0]) if lines_opt[0] else None
            end = int(lines_opt[1]) if lines_opt[1] else None
            text = "\n".join(text.splitlines()[start:end])
        except ValueError:
            _warn(f"{label}: unparseable :start-line:/:end-line: ignored")
    start_after = opts.get("start-after")
    if start_after:
        if start_after in text:
            text = text.split(start_after, 1)[1]
        else:
            _warn(f"{label}: :start-after: marker not found - ignored")
    end_before = opts.get("end-before")
    if end_before:
        if end_before in text:
            text = text.split(end_before, 1)[0]
        else:
            _warn(f"{label}: :end-before: marker not found - ignored")
    return text


def _include_target(ctx: _IncludeCtx, including: Path, arg: str, stack):
    """Resolve an include path, or warn and return None (directive kept).

    Paths are relative to the including file and must stay inside the
    repo root; absolute paths are rejected. Cycles, nesting deeper than
    INCLUDE_MAX_DEPTH and files over the remaining byte budget are refused.
    """
    label = f"{including.name}: include '{arg}'"
    if (
        not arg
        or arg.startswith(("/", "\\", "<"))
        or re.match(r"^[A-Za-z]:", arg)
    ):
        _warn(f"{label} rejected (absolute or system path) - directive kept")
        return None
    target = (including.parent / arg).resolve()
    if not target.is_relative_to(ctx.root):
        _warn(f"{label} rejected (escapes the repo root) - directive kept")
        return None
    if not target.is_file():
        _warn(f"{label} not found - directive kept")
        return None
    if target in stack:
        _warn(f"{label} is recursive - directive kept")
        return None
    if len(stack) > INCLUDE_MAX_DEPTH:
        _warn(
            f"{label} nests deeper than {INCLUDE_MAX_DEPTH} levels - "
            "directive kept"
        )
        return None
    size = target.stat().st_size
    if size > ctx.budget:
        _warn(f"{label} exceeds the text cap budget - directive kept")
        return None
    ctx.budget -= size
    ctx.inserted.add(target)
    return target


def _included_text(ctx, target: Path, opts: dict, literal: bool, stack,
                   label: str) -> str:
    text = target.read_text(encoding="utf-8", errors="replace")
    text = _slice_include(text, opts, label)
    if literal:
        return text.strip("\n")
    return _render_text(text, target, ctx, stack + [target])[0].strip("\n")


def _directive_block(lines, start: int, pad: int):
    """Collect option lines right after a directive; return (next, opts)."""
    opts = {}
    index = start
    while index < len(lines):
        line = lines[index]
        match = OPTION_RE.match(line)
        if not match or _indent(line) <= pad:
            break
        opts[match.group("key").strip().lower()] = (match.group("val") or "")
        index += 1
    return index, opts


def _render_rst(text: str, path: Path, ctx, stack, state: dict):
    """Resolve includes and reduce reST markup to readable text.

    Literal blocks (after `::`) and code directives are copied verbatim.
    Returns (text, orphan).
    """
    lines = text.splitlines()
    orphan = False
    # Leading field list (`:orphan:`, `:tocdepth: 2`) is build metadata.
    head = 0
    while head < len(lines) and (
        not lines[head].strip() or FIELD_RE.match(lines[head])
    ):
        if lines[head].strip() == ":orphan:":
            orphan = True
        head += 1
    if head and any(FIELD_RE.match(line) for line in lines[:head]):
        lines = lines[head:]
    out: list[str] = []
    literal = None  # indent owning a verbatim block
    skip = None  # indent owning a dropped block
    index = 0
    while index < len(lines):
        line = lines[index]
        blank = not line.strip()
        indent = _indent(line)
        if literal is not None:
            if blank or indent > literal:
                out.append(line)
                index += 1
                continue
            literal = None
        if skip is not None:
            if blank or indent > skip:
                index += 1
                continue
            skip = None
        if blank:
            if out and out[-1].strip():
                out.append("")
            index += 1
            continue
        match = DIRECTIVE_RE.match(line)
        if match:
            index, opts = _directive_block(lines, index + 1, indent)
            emitted, mode = _rst_directive(
                match, opts, path, ctx, stack, state
            )
            out.extend(emitted)
            if mode == "literal":
                literal = indent
            elif mode == "skip":
                skip = indent
            continue
        comment = COMMENT_RE.match(line)
        if comment:
            rest = (comment.group("rest") or "").strip()
            if rest.startswith("_") and re.match(r"^_[^:]*:$", rest):
                index += 1  # bare label target: `.. _quickstart:`
                continue
            if not rest.startswith(("_", "|", "[")):
                skip = indent  # comment block
                index += 1
                continue
            out.append(_simplify_roles(line))
            index += 1
            continue
        # Join a role wrapped across lines so it can be reduced whole.
        joins = 0
        while (
            joins < 3
            and ROLE_OPEN_RE.search(_simplify_roles(line))
            and index + 1 < len(lines)
            and lines[index + 1].strip()
        ):
            index += 1
            joins += 1
            line = line.rstrip() + " " + lines[index].strip()
        line = _simplify_roles(line)
        stripped = line.strip()
        if stripped.endswith("::") and not RST_RULE_RE.match(stripped):
            literal = indent
            if stripped == "::":
                index += 1
                continue
            line = line.rstrip()
            line = line[:-3] if line.endswith(" ::") else line[:-1]
        out.append(line)
        index += 1
    return "\n".join(out), orphan


def _rst_directive(match, opts, path, ctx, stack, state):
    """Render one directive line; return (lines, mode).

    mode: None (content rendered normally), "literal" (content verbatim)
    or "skip" (content dropped).
    """
    pad = match.group("pad")
    full_name = match.group("name").lower()
    name = full_name.rsplit(":", 1)[-1]
    arg = (match.group("arg") or "").strip()
    if name in ("include", "literalinclude"):
        label = f"{path.name}: {name} '{arg}'"
        target = _include_target(ctx, path, arg, stack)
        if target is None:
            original = [match.group(0).rstrip()]
            original += [f"{pad}   :{k}: {v}".rstrip() for k, v in opts.items()]
            return original, None
        literal = (
            name == "literalinclude"
            or "literal" in opts
            or "code" in opts
            or target.suffix.lower() not in (".rst", ".md", ".mdx", ".txt")
        )
        body = _included_text(ctx, target, opts, literal, stack, label)
        return [pad + l if l.strip() else "" for l in body.splitlines()], None
    if name in ("currentmodule", "module"):
        state["module"] = None if arg in ("", "None") else arg
        return [], "skip"
    if name in DROP_DIRECTIVES:
        return [], "skip"
    if name in AUTODOC_DIRECTIVES:
        target = arg.split("(", 1)[0].strip()
        module = state.get("module")
        if module and name != "automodule" and "." not in target:
            target = f"{module}.{target}"
        return [f"{pad}API reference: {target} (autodoc, see source)"], None
    if name in VERSION_DIRECTIVES:
        version, _, rest = arg.partition(" ")
        line = VERSION_DIRECTIVES[name].format(version)
        if rest.strip():
            line += " " + _simplify_roles(rest.strip())
        return [pad + line], None
    if name in ADMONITIONS:
        line = ADMONITIONS[name] + ":"
        if arg:
            line += " " + _simplify_roles(arg)
        return [pad + line], None
    if name in ("admonition", "group-tab", "tab", "topic", "sidebar"):
        return ([pad + _simplify_roles(arg) + ":"] if arg else []), None
    if name in UNWRAP_DIRECTIVES:
        return [], None
    if name in CODE_DIRECTIVES:
        return [match.group(0).rstrip()], "literal"
    if name in DOMAIN_OBJECTS:
        return [f"{pad}{arg} ({name})" if arg else ""], None
    return [match.group(0).rstrip()], None


def _render_md(text: str, path: Path, ctx, stack):
    """Resolve MyST ```{include}``` fences; everything else is untouched."""
    lines = text.splitlines()
    out: list[str] = []
    fence = None
    index = 0
    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if fence is not None:
            out.append(line)
            if set(stripped) == {fence[0]} and len(stripped) >= len(fence):
                fence = None
            index += 1
            continue
        match = MYST_INCLUDE_RE.match(line)
        if match:
            marker = match.group("fence")
            end = index + 1
            while end < len(lines) and not (
                set(lines[end].strip()) == {marker[0]}
                and len(lines[end].strip()) >= len(marker)
            ):
                end += 1
            opts = {}
            for opt_line in lines[index + 1:end]:
                opt = OPTION_RE.match(" " + opt_line.strip())
                if opt:
                    key = opt.group("key").strip().lower()
                    opts[key] = opt.group("val") or ""
            name = match.group("name")
            arg = match.group("arg")
            target = _include_target(ctx, path, arg, stack)
            if target is None:
                out.extend(lines[index:end + 1])
            else:
                literal = name == "literalinclude"
                body = _included_text(
                    ctx, target, opts, literal, stack, f"{path.name}: {arg}"
                )
                if literal:
                    lang = opts.get("language", "")
                    body = f"{marker}{lang}\n{body}\n{marker}"
                out.extend(body.splitlines())
            index = end + 1
            continue
        if stripped.startswith(FENCE_PREFIXES):
            run = len(stripped) - len(stripped.lstrip(stripped[0]))
            fence = stripped[0] * run
        out.append(line)
        index += 1
    return "\n".join(out), False


def _render_text(text: str, path: Path, ctx, stack):
    suffix = path.suffix.lower()
    if suffix == ".rst":
        return _render_rst(text, path, ctx, stack, {"module": None})
    if suffix in (".md", ".mdx"):
        return _render_md(text, path, ctx, stack)
    return text, False


# --- Reading order: Sphinx toctree / MkDocs nav -------------------------------

MKDOCS_NAV_PATH_RE = re.compile(
    r"""(?:^\s*-\s*|:\s+)['"]?"""
    r"""(?P<path>[^'"\s:]+\.(?:md|mdx|rst|markdown))['"]?\s*$"""
)
DOCS_DIR_RE = re.compile(r"""^docs_dir:\s*['"]?([^'"#\s]+)['"]?\s*(?:#.*)?$""")


def _toctree_entries(text: str, is_md: bool) -> list[str]:
    """Document references listed in `.. toctree::` / ```{toctree}``` blocks."""
    entries = []
    lines = text.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        block_pad = None
        fence = None
        if is_md:
            match = re.match(r"^\s*(`{3,}|~{3,})\{toctree\}", line)
            if match:
                fence = match.group(1)
        else:
            match = DIRECTIVE_RE.match(line)
            if match and match.group("name").lower() == "toctree":
                block_pad = _indent(line)
        index += 1
        if fence is None and block_pad is None:
            continue
        while index < len(lines):
            body = lines[index]
            stripped = body.strip()
            if fence is not None and stripped.startswith(fence):
                index += 1
                break
            if (
                block_pad is not None
                and stripped
                and _indent(body) <= block_pad
            ):
                break
            index += 1
            if not stripped or stripped.startswith((":", "---", "#")):
                continue
            explicit = EXPLICIT_TITLE_RE.match(stripped)
            entry = explicit.group("target") if explicit else stripped
            if (
                entry == "self"
                or "*" in entry
                or "://" in entry
                or entry.startswith(("http:", "https:", "mailto:"))
            ):
                continue
            entries.append(entry)
    return entries


def _sphinx_order(root: Path, by_key: dict) -> list[Path]:
    order: list[Path] = []
    for dir_name in DOC_DIRS:
        start = f"{dir_name}/index"
        if start not in by_key:
            continue
        seen: set[str] = set()
        stack = [start]
        # Iterative DFS: push children reversed so they pop in order.
        while stack:
            key = stack.pop()
            if key in seen or key not in by_key:
                continue
            seen.add(key)
            path = by_key[key]
            order.append(path)
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            base = posixpath.dirname(key)
            children = []
            for entry in _toctree_entries(text, path.suffix.lower() != ".rst"):
                if entry.startswith("/"):
                    child = posixpath.join(dir_name, entry.lstrip("/"))
                else:
                    child = posixpath.join(base, entry)
                child = posixpath.normpath(child)
                stem, ext = posixpath.splitext(child)
                if ext.lower() in DOC_SUFFIXES:
                    child = stem
                children.append(child)
            stack.extend(reversed(children))
        if order:
            break
    return order


def _mkdocs_order(root: Path, by_rel: dict) -> list[Path]:
    """Files in `nav:` order from mkdocs.yml; [] when absent/unparseable.

    Only the simple YAML subset MkDocs nav uses is understood (block
    lists of `- Title: path.md` / `- path.md`); anything else yields [].
    """
    for name in ("mkdocs.yml", "mkdocs.yaml"):
        config_path = root / name
        if config_path.is_file():
            break
    else:
        return []
    try:
        lines = config_path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return []
    docs_dir = "docs"
    for line in lines:
        match = DOCS_DIR_RE.match(line)
        if match:
            docs_dir = posixpath.normpath(match.group(1).strip("/"))
    try:
        start = next(
            i for i, line in enumerate(lines)
            if re.match(r"^nav:\s*(?:#.*)?$", line)
        )
    except StopIteration:
        return []
    order: list[Path] = []
    for line in lines[start + 1:]:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if _indent(line) == 0 and not stripped.startswith("-"):
            break
        match = MKDOCS_NAV_PATH_RE.search(line)
        if not match:
            continue
        rel = posixpath.normpath(posixpath.join(docs_dir, match.group("path")))
        path = by_rel.get(rel)
        if path is not None and path not in order:
            order.append(path)
    return order


def _order_docs(root: Path, docs: list[Path]) -> list[Path]:
    """Reading order: mkdocs nav, else Sphinx toctree walk, else filenames.

    Docs the navigation does not reach follow in filename order.
    """
    by_rel = {p.relative_to(root).as_posix(): p for p in docs}
    by_key = {}
    for rel, path in by_rel.items():
        by_key.setdefault(posixpath.splitext(rel)[0], path)
    order = _mkdocs_order(root, by_rel) or _sphinx_order(root, by_key)
    reached = set(order)
    return order + [p for p in docs if p not in reached]


def parse(source: str):
    match = REPO_URL_RE.match(source)
    if not match:
        raise ExtractError(
            f"Not a GitHub repository URL: {source}\n"
            "Expected https://github.com/<owner>/<repo> (no deeper paths)."
        )
    owner = match.group("owner")
    repo_name = match.group("repo").removesuffix(".git")
    tar_path = _download(owner, repo_name)
    dest = config.work_dir() / f"repo-{owner}-{repo_name}"
    _extract(tar_path, dest)
    root = _repo_root(dest)
    files = _select_files(root)
    if not files:
        raise ExtractError(
            f"{owner}/{repo_name} has no README or Markdown docs.\n"
            "The repo parser reads root README* files, top-level *.md and "
            "docs/ or doc/ (*.md, *.mdx, *.rst) - this repository has none "
            "to extract."
        )
    rendered = []
    for path in files:
        rel_path = path.relative_to(root).as_posix()
        ctx = _IncludeCtx(root, config.REPO_TEXT_CAP_BYTES)
        try:
            resolved = path.resolve()
        except OSError:
            resolved = path
        text = path.read_text(encoding="utf-8", errors="replace")
        text, orphan = _render_text(text, path, ctx, [resolved])
        rendered.append((path, rel_path, resolved, text, orphan, ctx.inserted))
    # A file whose content was already inserted into another kept file via
    # include is not repeated as its own segment (CHANGES.md pulled into
    # docs/changes.md). Biggest includers claim their files first.
    covered: set[Path] = set()
    duplicates: set[str] = set()
    for _, rel_path, resolved, _, _, inserted in sorted(
        rendered, key=lambda item: -len(item[5])
    ):
        if resolved in covered:
            duplicates.add(rel_path)
        else:
            covered |= inserted
    chunks = []
    segments = []
    dropped = []
    offset = 0
    total_bytes = 0
    for path, rel_path, _, text, orphan, _ in rendered:
        if rel_path in duplicates:
            continue
        body = text.strip()
        size = len(body.encode("utf-8"))
        # The first file (normally the README) is always kept so a huge
        # README alone can never produce an empty extraction.
        if chunks and total_bytes + size > config.REPO_TEXT_CAP_BYTES:
            dropped.append(rel_path)
            continue
        total_bytes += size
        title = _title(body, rel_path)
        chunk = f"=== {title} ===\n{body}\n\n"
        segment = {
            "title": title, "start_s": None, "pages": None,
            "offset": offset, "path": rel_path,
        }
        if orphan:
            segment["orphan"] = True
        if len(body) < STUB_CHARS:
            segment["stub"] = True
        segments.append(segment)
        chunks.append(chunk)
        offset += len(chunk)
    if dropped:
        _warn(
            f"{owner}/{repo_name}: text cap of "
            f"{config.REPO_TEXT_CAP_BYTES} bytes reached - dropped "
            f"{len(dropped)} file(s): {', '.join(dropped)}.\n"
            "The extracted docs are incomplete."
        )
    full_text = "".join(chunks)
    words = len(full_text.split())
    metadata = {
        "source_type": "repo",
        "title": f"{owner}/{repo_name}",
        "owner": owner,
        "repo": repo_name,
        "origin": source,
        "file_count": len(segments),
        "words": words,
        "est_tokens": utils.estimate_tokens(words),
        "segments": segments,
    }
    return full_text, metadata
