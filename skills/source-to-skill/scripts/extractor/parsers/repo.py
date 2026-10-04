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
    return readmes + top_md + docs_md


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
    chunks = []
    segments = []
    dropped = []
    offset = 0
    total_bytes = 0
    for path in files:
        text = path.read_text(encoding="utf-8", errors="replace")
        size = len(text.encode("utf-8"))
        # The first file (normally the README) is always kept so a huge
        # README alone can never produce an empty extraction.
        if chunks and total_bytes + size > config.REPO_TEXT_CAP_BYTES:
            dropped.append(path.relative_to(root).as_posix())
            continue
        total_bytes += size
        rel_path = path.relative_to(root).as_posix()
        title = _title(text, rel_path)
        chunk = f"=== {title} ===\n{text.strip()}\n\n"
        segments.append(
            {
                "title": title, "start_s": None, "pages": None,
                "offset": offset, "path": rel_path,
            }
        )
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
