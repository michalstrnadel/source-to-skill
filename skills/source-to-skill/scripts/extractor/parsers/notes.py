"""Local notes-folder parser: Obsidian vaults, Markdown folders, Logseq pages.

Collects .md/.markdown/.mdx/.txt/.rst files recursively (hidden and tool
folders skipped), one segment per note. YAML frontmatter is stripped
(title and tags kept), Obsidian [[wikilinks]] become plain text and are
recorded per note, so the generator can find the hub notes.
"""
import os
import re
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import unquote

from .. import config, utils
from ..utils import ExtractError
from . import repo

NOTE_SUFFIXES = (".md", ".markdown", ".mdx", ".txt", ".rst")
# Tool and dependency folders that never hold the user's notes. Hidden
# folders (.obsidian, .git, .trash, .logseq) are skipped by their dot.
SKIP_DIRS = {"node_modules", "__pycache__", "venv", "site-packages"}
# Logseq keeps backups and page history next to the pages.
SKIP_REL_DIRS = {"logseq/bak", "logseq/version-files"}
FIRST_FILES = ("readme", "index", "_index", "home")
FENCE_PREFIXES = ("```", "~~~")
BINARY_SNIFF_BYTES = 8192
HUB_LIMIT = 10
HUB_MIN_INBOUND = 2

FRONTMATTER_RE = re.compile(
    r"\A---[ \t]*\n(.*?\n)?(?:---|\.\.\.)[ \t]*(?:\n|\Z)", re.S
)
WIKILINK_RE = re.compile(r"(!?)\[\[([^\[\]\n]+?)\]\]")
# Relative Markdown links to other notes: [text](sub/note.md#part).
# URLs (scheme:), absolute paths and same-page anchors are not notes.
MD_LINK_RE = re.compile(
    r"\[[^\]\n]*\]\((?![a-z][a-z0-9+.-]*:|/|#)"
    r"([^)\s]+?\.(?:md|markdown|mdx))(?:#[^)\s]*)?\)",
    re.I,
)
YAML_KEY_RE = re.compile(r"^([A-Za-z_][\w-]*):[ \t]*(.*)$")
YAML_ITEM_RE = re.compile(r"^[ \t]+-[ \t]*(.*)$|^-[ \t]+(.*)$")


def _warn(message: str) -> None:
    print(f"WARNING: {message}", file=sys.stderr)


def _display(path: Path) -> str:
    """The path as shown in outputs: never an absolute home path."""
    text = str(path)
    home = str(Path.home())
    if text == home:
        return "~"
    if text.startswith(home + os.sep):
        return "~" + text[len(home):]
    return text


def _sort_key(name: str):
    stem = name.rsplit(".", 1)[0].lower()
    return (stem not in FIRST_FILES, name.lower())


def _collect(root: Path) -> list[Path]:
    """Note files in reading order: each folder's files, then subfolders."""
    files = []

    def walk(folder: Path):
        try:
            entries = list(os.scandir(folder))
        except OSError as err:
            _warn(f"cannot read folder {folder.relative_to(root)}: {err}")
            return
        subdirs = []
        here = []
        for entry in entries:
            if entry.name.startswith("."):
                continue
            path = Path(entry.path)
            if entry.is_symlink():
                # Never follow links out of the folder the user named.
                try:
                    path.resolve().relative_to(root)
                except (OSError, ValueError):
                    continue
            if entry.is_dir():
                rel = path.relative_to(root).as_posix()
                if not (
                    entry.name in SKIP_DIRS or rel in SKIP_REL_DIRS
                    or entry.is_symlink()
                ):
                    subdirs.append(path)
            elif entry.is_file() and entry.name.lower().endswith(NOTE_SUFFIXES):
                here.append(path)
        here.sort(key=lambda p: _sort_key(p.name))
        files.extend(here)
        for sub in sorted(subdirs, key=lambda p: p.name.lower()):
            walk(sub)

    walk(root)
    return files


def _unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def _frontmatter(text: str):
    """(fields, body): a tiny YAML subset - scalars and string lists."""
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}, text
    fields = {}
    key = None
    for line in (match.group(1) or "").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        item = YAML_ITEM_RE.match(line)
        if item and key is not None:
            value = _unquote(item.group(1) or item.group(2) or "")
            if not isinstance(fields.get(key), list):
                fields[key] = []
            if value:
                fields[key].append(value)
            continue
        pair = YAML_KEY_RE.match(line)
        if not pair:
            key = None
            continue
        key, value = pair.group(1).lower(), pair.group(2).strip()
        if value.startswith("[") and value.endswith("]"):
            fields[key] = [
                _unquote(v) for v in value[1:-1].split(",") if v.strip()
            ]
        else:
            fields[key] = _unquote(value)
    return fields, text[match.end():]


def _tags(fields: dict) -> list[str]:
    raw = fields.get("tags", fields.get("tag"))
    if isinstance(raw, str):
        raw = re.split(r"[,\s]+", raw)
    tags = []
    for tag in raw or []:
        tag = tag.strip().lstrip("#")
        if tag and tag not in tags:
            tags.append(tag)
    return tags


def _wikilink(match, links: list) -> str:
    embed, inner = match.group(1), match.group(2)
    target, _, alias = inner.partition("|")
    target = target.strip()
    if embed:
        return f"[embed: {target.split('#')[0].strip() or target}]"
    note, _, heading = target.partition("#")
    note, heading = note.strip(), heading.strip().lstrip("^")
    if note and note not in links:
        links.append(note)
    if alias.strip():
        return alias.strip()
    if note and heading:
        return f"{note} > {heading}"
    return note or heading


def _md_link_target(rel_dir: str, target: str):
    """A relative Markdown link as a note path without its suffix."""
    joined = os.path.normpath(os.path.join(rel_dir, unquote(target)))
    if joined.startswith(".."):
        return None
    return Path(joined).with_suffix("").as_posix()


def _render(text: str, rel_path: str):
    """(text, links): wikilinks reduced to text outside code fences."""
    links = []
    rel_dir = Path(rel_path).parent.as_posix().removeprefix(".")
    out = []
    fence = None
    for line in text.splitlines():
        stripped = line.lstrip()
        if fence is not None:
            out.append(line)
            if stripped.startswith(fence):
                fence = None
            continue
        if stripped.startswith(FENCE_PREFIXES):
            fence = stripped[:3]
            out.append(line)
            continue
        for match in MD_LINK_RE.finditer(line):
            target = _md_link_target(rel_dir, match.group(1))
            if target and target not in links:
                links.append(target)
        out.append(WIKILINK_RE.sub(lambda m: _wikilink(m, links), line))
    return "\n".join(out), links


def _title(fields: dict, body: str, rel_path: str) -> str:
    title = fields.get("title")
    if isinstance(title, str) and title.strip():
        return " ".join(title.split())
    found = repo._title(body, rel_path)
    if found != rel_path:
        return found
    return Path(rel_path).stem


def _read(path: Path, rel_path: str):
    """File text, or None (with a warning) for huge or binary files."""
    try:
        size = path.stat().st_size
        if size > config.NOTES_MAX_FILE_BYTES:
            _warn(
                f"skipped {rel_path}: {size} bytes is over the "
                f"{config.NOTES_MAX_FILE_BYTES}-byte note limit"
            )
            return None
        raw = path.read_bytes()
    except OSError as err:
        _warn(f"skipped {rel_path}: {err}")
        return None
    if b"\x00" in raw[:BINARY_SNIFF_BYTES]:
        _warn(f"skipped {rel_path}: binary content")
        return None
    text = raw.decode("utf-8", errors="replace")
    return text.replace("\r\n", "\n").replace("\r", "\n").lstrip("﻿")


def _hubs(segments) -> list[dict]:
    """Notes with the most inbound links (wikilinks and Markdown links)."""
    by_path = {}
    by_stem = {}
    for seg in segments:
        no_suffix = Path(seg["path"]).with_suffix("").as_posix().lower()
        by_path[no_suffix] = seg["path"]
        # Obsidian resolves a bare name to the shortest matching path.
        stem = Path(seg["path"]).stem.lower()
        if stem not in by_stem or len(seg["path"]) < len(by_stem[stem]):
            by_stem[stem] = seg["path"]
    inbound = Counter()
    for seg in segments:
        targets = set()
        for link in seg.get("links", []):
            key = link.lower()
            target = by_path.get(key) or by_stem.get(key.rsplit("/", 1)[-1])
            if target and target != seg["path"]:
                targets.add(target)
        inbound.update(targets)
    titles = {seg["path"]: seg["title"] for seg in segments}
    ranked = sorted(
        (item for item in inbound.items() if item[1] >= HUB_MIN_INBOUND),
        key=lambda item: (-item[1], item[0].lower()),
    )
    return [
        {"title": titles[path], "path": path, "inbound": count}
        for path, count in ranked[:HUB_LIMIT]
    ]


def parse(source: str):
    root = Path(source).expanduser()
    if not root.is_dir():
        raise ExtractError(
            f"{_display(root)} is not a directory.\n"
            "Pass the folder that holds the notes (an Obsidian vault, a "
            "Markdown docs folder, Logseq's pages/)."
        )
    root = root.resolve()
    files = _collect(root)
    chunks = []
    segments = []
    dropped = []
    tag_counts = Counter()
    offset = 0
    total_bytes = 0
    for path in files:
        rel_path = path.relative_to(root).as_posix()
        text = _read(path, rel_path)
        if text is None:
            continue
        fields, body = ({}, text)
        if not rel_path.lower().endswith((".txt", ".rst")):
            fields, body = _frontmatter(text)
        body, links = _render(body.strip(), rel_path)
        body = body.strip()
        if not body:
            continue
        size = len(body.encode("utf-8"))
        # The first note is always kept so one huge note never yields
        # an empty extraction.
        if chunks and total_bytes + size > config.NOTES_TEXT_CAP_BYTES:
            dropped.append(rel_path)
            continue
        total_bytes += size
        title = _title(fields, body, rel_path)
        segment = {
            "title": title, "start_s": None, "pages": None,
            "offset": offset, "path": rel_path, "key": rel_path,
        }
        tags = _tags(fields)
        if tags:
            segment["tags"] = tags
            tag_counts.update(tags)
        if links:
            segment["links"] = links
        chunk = f"=== {title} ===\n{body}\n\n"
        segments.append(segment)
        chunks.append(chunk)
        offset += len(chunk)
    if dropped:
        _warn(
            f"text cap of {config.NOTES_TEXT_CAP_BYTES} bytes reached - "
            f"dropped {len(dropped)} note(s): {', '.join(dropped[:20])}"
            f"{' ...' if len(dropped) > 20 else ''}.\n"
            "The extracted notes are incomplete - extract a subfolder to "
            "cover the rest."
        )
    if not segments:
        raise ExtractError(
            f"No notes found in {_display(root)}.\n"
            "The notes parser reads non-empty .md, .markdown, .mdx, .txt "
            "and .rst files (hidden folders such as .obsidian and .trash "
            "are skipped)."
        )
    full_text = "".join(chunks)
    words = len(full_text.split())
    metadata = {
        "source_type": "notes",
        "title": root.name or "Notes",
        "origin": _display(root),
        "file_count": len(segments),
        "tags": dict(sorted(tag_counts.items(), key=lambda t: (-t[1], t[0]))),
        "hubs": _hubs(segments),
        "words": words,
        "est_tokens": utils.estimate_tokens(words),
        "segments": segments,
    }
    return full_text, metadata
