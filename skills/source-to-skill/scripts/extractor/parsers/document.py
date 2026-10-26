"""Document parser: Word, PowerPoint and OpenDocument files via stdlib.

.docx/.pptx (Office Open XML) and .odt/.odp (OpenDocument) are zip
archives of XML parts, so zipfile + ElementTree read them without any
third-party library. Word documents segment at level-1/2 headings (by
style or outline level); presentations get one segment per slide in
presentation order, with the speaker notes appended under `Notes:`.
Footnotes, comments and tracked deletions are left out.
"""
import posixpath
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree

from .. import utils
from ..utils import ExtractError

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
P = "{http://schemas.openxmlformats.org/presentationml/2006/main}"
R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
PKG_REL = "{http://schemas.openxmlformats.org/package/2006/relationships}"
TEXT = "{urn:oasis:names:tc:opendocument:xmlns:text:1.0}"
TABLE = "{urn:oasis:names:tc:opendocument:xmlns:table:1.0}"
DRAW = "{urn:oasis:names:tc:opendocument:xmlns:drawing:1.0}"
PRES = "{urn:oasis:names:tc:opendocument:xmlns:presentation:1.0}"
OFFICE = "{urn:oasis:names:tc:opendocument:xmlns:office:1.0}"

MAIN_PART = {
    "docx": "word/document.xml",
    "pptx": "ppt/presentation.xml",
    "odt": "content.xml",
    "odp": "content.xml",
}
LEGACY_FORMATS = {".doc": ".docx", ".ppt": ".pptx", ".rtf": ".docx"}

# Word inline elements whose content is never body text: tracked
# deletions, field codes, footnote/endnote/comment references, and the
# fallback copy of mc:AlternateContent (the Choice is read instead).
DOCX_SKIP = {
    "del", "delText", "instrText", "footnoteReference", "endnoteReference",
    "commentReference", "rPr", "pPr", "fldChar", "Fallback",
}
# Slide placeholders that hold chrome, not content.
PPTX_CHROME_PH = {"dt", "ftr", "hdr", "sldNum", "sldImg"}
PPTX_TITLE_PH = {"title", "ctrTitle"}
# OpenDocument elements whose content is not body text: footnotes,
# comments, change tracking, generated tables of contents.
ODF_SKIP = {
    "note", "annotation", "tracked-changes", "table-of-content",
    "sequence-decls", "bookmark-ref",
}
ODF_CHROME_CLASSES = {"page-number", "date-time", "footer", "header"}

HEADING_NAME_RE = re.compile(r"(?i)^heading\s*(\d)$")
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")


def _local(tag) -> str:
    return tag.rsplit("}", 1)[-1] if isinstance(tag, str) else ""


def _clean_lines(text: str) -> str:
    """Collapse whitespace per line and drop empty lines."""
    lines = (" ".join(line.split()) for line in text.split("\n"))
    return "\n".join(line for line in lines if line)


def pipe_table(rows) -> str:
    """Render rows of cell strings as `| a | b |` lines (header rule after
    the first row). One-column/layout tables come back as plain lines."""
    rows = [
        [" ".join(cell.split()).replace("|", "\\|") for cell in row]
        for row in rows
    ]
    rows = [row for row in rows if any(row)]
    if not rows:
        return ""
    if all(sum(1 for cell in row if cell) <= 1 for row in rows):
        return "\n".join(cell for row in rows for cell in row if cell)
    width = max(len(row) for row in rows)
    lines = []
    for index, row in enumerate(rows):
        row = row + [""] * (width - len(row))
        lines.append("| " + " | ".join(row) + " |")
        if index == 0:
            lines.append("| " + " | ".join(["---"] * width) + " |")
    return "\n".join(lines)


def _image_marker(alt) -> str:
    alt = " ".join((alt or "").split())
    return f"\n[image: {alt}]\n" if alt else ""


def _xml(zf, name: str, path: Path):
    try:
        return ElementTree.fromstring(zf.read(name))
    except ElementTree.ParseError as err:
        raise ExtractError(
            f"{path}: cannot parse {name} ({err}).\n"
            "The file is malformed - re-save it from its editor and retry."
        ) from err


def _optional_xml(zf, name: str, path: Path):
    return _xml(zf, name, path) if name in zf.namelist() else None


def _first(root, *names):
    """Text of the first element (any namespace) with one of `names`."""
    if root is None:
        return None
    for name in names:
        for el in root.iter():
            if _local(el.tag) == name and el.text and el.text.strip():
                return " ".join(el.text.split())
    return None


def _properties(root) -> dict:
    """title/author/date/language from docProps/core.xml or ODF meta.xml."""
    created = _first(root, "created", "creation-date")
    match = DATE_RE.match(created or "")
    return {
        "title": _first(root, "title"),
        "author": _first(root, "creator", "initial-creator"),
        "date": match.group(0) if match else None,
        "language": _first(root, "language"),
    }


def _sections(items):
    """[(title or None, body)] split at heading items, like article.py."""
    sections = []
    title, parts = None, []
    for kind, payload in items:
        if kind == "heading":
            sections.append((title, "\n".join(parts)))
            title, parts = payload, []
        else:
            parts.append(payload)
    sections.append((title, "\n".join(parts)))
    if len(sections) > 1 and sections[0] == (None, ""):
        sections = sections[1:]
    return [
        (
            title or ("Full text" if len(sections) == 1 else "Introduction"),
            body,
        )
        for title, body in sections
    ]


# --- Word -------------------------------------------------------------------


def _docx_styles(zf, path: Path) -> dict:
    """{style id: {name, outline, list, based_on}} from word/styles.xml."""
    root = _optional_xml(zf, "word/styles.xml", path)
    styles = {}
    if root is None:
        return styles
    for style in root.iter(W + "style"):
        style_id = style.get(W + "styleId")
        if not style_id:
            continue
        name_el = style.find(W + "name")
        outline = style.find(f"{W}pPr/{W}outlineLvl")
        based = style.find(W + "basedOn")
        styles[style_id] = {
            "name": (name_el.get(W + "val") or "") if name_el is not None else "",
            "outline": outline.get(W + "val") if outline is not None else None,
            "list": style.find(f"{W}pPr/{W}numPr") is not None,
            "based_on": based.get(W + "val") if based is not None else None,
        }
    return styles


def _style_heading_level(style_id, styles):
    """Heading level of a paragraph style (1-9), following basedOn."""
    seen = set()
    current = style_id
    while current and current not in seen:
        seen.add(current)
        style = styles.get(current)
        if style is None:
            # No styles.xml entry: trust Word's built-in ids (Heading1).
            match = HEADING_NAME_RE.match(current)
            return int(match.group(1)) if match else None
        match = HEADING_NAME_RE.match(style["name"])
        if match:
            return int(match.group(1))
        if style["outline"] is not None and style["outline"].isdigit():
            level = int(style["outline"]) + 1
            return level if level <= 9 else None
        current = style["based_on"]
    return None


def _docx_inline(el, out):
    for child in el:
        name = _local(child.tag)
        if name in DOCX_SKIP:
            continue
        if name == "t":
            out.append(child.text or "")
        elif name in ("tab", "ptab"):
            out.append(" ")
        elif name in ("br", "cr"):
            out.append("\n")
        elif name == "AlternateContent":
            choice = next(
                (c for c in child if _local(c.tag) == "Choice"), None
            )
            if choice is not None:
                _docx_inline(choice, out)
        elif name == "drawing":
            doc_pr = next(
                (d for d in child.iter() if _local(d.tag) == "docPr"), None
            )
            if doc_pr is not None:
                out.append(
                    _image_marker(doc_pr.get("descr") or doc_pr.get("title"))
                )
            for box in child.iter(W + "txbxContent"):
                for para in box.iter(W + "p"):
                    out.append("\n")
                    _docx_inline(para, out)
                    out.append("\n")
        elif name == "txbxContent":
            for para in child.iter(W + "p"):
                out.append("\n")
                _docx_inline(para, out)
                out.append("\n")
        else:
            _docx_inline(child, out)


def _docx_para_text(para) -> str:
    out = []
    _docx_inline(para, out)
    return _clean_lines("".join(out))


def _docx_table(tbl) -> str:
    rows = []
    for tr in tbl.findall(W + "tr"):
        cells = []
        for tc in tr.findall(W + "tc"):
            texts = [_docx_para_text(p) for p in tc.iter(W + "p")]
            cells.append(" ".join(t for t in texts if t))
        rows.append(cells)
    return pipe_table(rows)


def _docx_items(container, styles, items):
    """Append ("heading"|"text"|"title", payload) items in body order."""
    for child in container:
        name = _local(child.tag)
        if name == "tbl":
            table = _docx_table(child)
            if table:
                items.append(("text", table))
        elif name in ("sdt", "customXml", "sdtContent", "smartTag"):
            _docx_items(child, styles, items)
        elif name == "p":
            text = _docx_para_text(child)
            if not text:
                continue
            ppr = child.find(W + "pPr")
            style_id = None
            level = None
            list_level = None
            if ppr is not None:
                style_el = ppr.find(W + "pStyle")
                style_id = style_el.get(W + "val") if style_el is not None else None
                outline = ppr.find(W + "outlineLvl")
                if outline is not None and (outline.get(W + "val") or "").isdigit():
                    level = int(outline.get(W + "val")) + 1
                num = ppr.find(W + "numPr")
                if num is not None:
                    ilvl = num.find(W + "ilvl")
                    value = ilvl.get(W + "val") if ilvl is not None else "0"
                    list_level = int(value) if (value or "").isdigit() else 0
            style = styles.get(style_id) or {}
            if level is None and style_id:
                level = _style_heading_level(style_id, styles)
            style_name = (style.get("name") or style_id or "").lower()
            if style_name == "title":
                items.append(("title", text))
            elif level is not None and level <= 2:
                items.append(("heading", " ".join(text.split())))
            elif list_level is not None or style.get("list") or (
                style_name.startswith(("list bullet", "list number"))
            ):
                if list_level is None:
                    # "List Bullet 2" carries its nesting in the style name.
                    match = re.search(r"\s(\d)$", style_name)
                    list_level = int(match.group(1)) - 1 if match else 0
                indent = "  " * list_level
                items.append(("text", indent + "- " + text))
            else:
                items.append(("text", text))


def _parse_docx(zf, path: Path):
    root = _xml(zf, MAIN_PART["docx"], path)
    body = root.find(W + "body")
    items = []
    if body is not None:
        _docx_items(body, _docx_styles(zf, path), items)
    props = _properties(_optional_xml(zf, "docProps/core.xml", path))
    style_titles = [payload for kind, payload in items if kind == "title"]
    title = props["title"] or (style_titles[0] if style_titles else None)
    items = [
        ("text", payload) if kind == "title" else (kind, payload)
        for kind, payload in items
        if not (kind == "title" and payload == title)
    ]
    return _sections(items), props, title, {}


# --- PowerPoint -------------------------------------------------------------


def _rels(zf, part: str, path: Path) -> dict:
    """{rel id: (type, zip path)} for an OOXML part."""
    rels_name = posixpath.join(
        posixpath.dirname(part), "_rels", posixpath.basename(part) + ".rels"
    )
    root = _optional_xml(zf, rels_name, path)
    rels = {}
    if root is None:
        return rels
    for rel in root.iter(PKG_REL + "Relationship"):
        target = rel.get("Target") or ""
        if rel.get("TargetMode") == "External" or not target:
            continue
        if target.startswith("/"):
            resolved = target.lstrip("/")
        else:
            resolved = posixpath.normpath(
                posixpath.join(posixpath.dirname(part), target)
            )
        rels[rel.get("Id")] = (rel.get("Type") or "", resolved)
    return rels


def _pptx_para(para, bullets: bool) -> str:
    out = []
    for el in para.iter():
        name = _local(el.tag)
        if name == "t":
            out.append(el.text or "")
        elif name == "br":
            out.append(" ")
    text = " ".join("".join(out).split())
    if not text:
        return ""
    ppr = para.find(A + "pPr")
    level = 0
    if ppr is not None:
        level = int(ppr.get("lvl")) if (ppr.get("lvl") or "").isdigit() else 0
        if ppr.find(A + "buNone") is not None:
            bullets = False
        elif ppr.find(A + "buChar") is not None or ppr.find(A + "buAutoNum") is not None:
            bullets = True
    return ("  " * level + "- " + text) if bullets else text


def _pptx_table(tbl) -> str:
    rows = []
    for tr in tbl.iter(A + "tr"):
        cells = []
        for tc in tr.findall(A + "tc"):
            texts = [_pptx_para(p, False) for p in tc.iter(A + "p")]
            cells.append(" ".join(t for t in texts if t))
        rows.append(cells)
    return pipe_table(rows)


def _pptx_shapes(tree, out: dict, notes: bool = False):
    """Walk a shape tree; fill out["title"] and out["lines"]."""
    for shape in tree:
        name = _local(shape.tag)
        if name == "grpSp":
            _pptx_shapes(shape, out, notes)
        elif name == "graphicFrame" and not notes:
            for tbl in shape.iter(A + "tbl"):
                table = _pptx_table(tbl)
                if table:
                    out["lines"].append(table)
        elif name == "pic" and not notes:
            c_nv = next((e for e in shape.iter() if _local(e.tag) == "cNvPr"), None)
            if c_nv is not None:
                marker = _image_marker(c_nv.get("descr")).strip()
                if marker:
                    out["lines"].append(marker)
        elif name == "sp":
            ph = shape.find(f"{P}nvSpPr/{P}nvPr/{P}ph")
            ph_type = ph.get("type") if ph is not None else None
            if ph_type in PPTX_CHROME_PH:
                continue
            if notes and (ph is None or ph_type not in (None, "body")):
                continue
            body = shape.find(P + "txBody")
            if body is None:
                continue
            if ph_type in PPTX_TITLE_PH and not notes:
                texts = [_pptx_para(p, False) for p in body.findall(A + "p")]
                title = " ".join(t for t in texts if t)
                if title and not out["title"]:
                    out["title"] = title
                    continue
                if title:
                    out["lines"].append(title)
                continue
            bullets = (
                not notes and ph is not None and ph_type in (None, "body", "obj")
            )
            for para in body.findall(A + "p"):
                line = _pptx_para(para, bullets)
                if line:
                    out["lines"].append(line)


def _pptx_slide_parts(zf, path: Path) -> list:
    pres = _xml(zf, MAIN_PART["pptx"], path)
    rels = _rels(zf, MAIN_PART["pptx"], path)
    parts = []
    for sld in pres.iter(P + "sldId"):
        rel = rels.get(sld.get(R + "id"))
        if rel and rel[1] in zf.namelist():
            parts.append(rel[1])
    if not parts:
        # No (readable) slide list: fall back to file numbering.
        numbered = [
            n for n in zf.namelist()
            if re.match(r"ppt/slides/slide\d+\.xml$", n)
        ]
        parts = sorted(numbered, key=lambda n: int(re.findall(r"\d+", n)[-1]))
    return parts


def _parse_pptx(zf, path: Path):
    sections = []
    flags = {}
    for number, part in enumerate(_pptx_slide_parts(zf, path), start=1):
        slide = _xml(zf, part, path)
        out = {"title": None, "lines": []}
        tree = slide.find(f"{P}cSld/{P}spTree")
        if tree is not None:
            _pptx_shapes(tree, out)
        notes = {"title": None, "lines": []}
        for rel_type, target in _rels(zf, part, path).values():
            if rel_type.endswith("/notesSlide") and target in zf.namelist():
                notes_tree = _xml(zf, target, path).find(f"{P}cSld/{P}spTree")
                if notes_tree is not None:
                    _pptx_shapes(notes_tree, notes, notes=True)
        body = "\n".join(out["lines"])
        if notes["lines"]:
            body += ("\n\n" if body else "") + "Notes:\n" + "\n".join(notes["lines"])
        sections.append((out["title"] or f"Slide {number}", body))
        flags[len(sections) - 1] = {"slide": number}
        if slide.get("show") == "0":
            flags[len(sections) - 1]["hidden"] = True
    props = _properties(_optional_xml(zf, "docProps/core.xml", path))
    return sections, props, props["title"], flags


# --- OpenDocument -----------------------------------------------------------


def _odf_inline(el, out):
    if el.text:
        out.append(el.text)
    for child in el:
        name = _local(child.tag)
        if name in ODF_SKIP:
            pass
        elif name == "s":
            count = child.get(TEXT + "c") or "1"
            out.append(" " * (int(count) if count.isdigit() else 1))
        elif name == "tab":
            out.append(" ")
        elif name == "line-break":
            out.append("\n")
        elif name == "frame":
            out.append(_odf_image(child))
        else:
            _odf_inline(child, out)
        if child.tail:
            out.append(child.tail)


def _odf_image(frame) -> str:
    alt = None
    for el in frame:
        if _local(el.tag) in ("title", "desc") and el.text:
            alt = alt or el.text
    return _image_marker(alt) if frame.find(DRAW + "image") is not None else ""


def _odf_text(el) -> str:
    out = []
    _odf_inline(el, out)
    return _clean_lines("".join(out))


def _odf_table(table) -> str:
    rows = []
    for row in table.iter(TABLE + "table-row"):
        rows.append([
            " ".join(t for t in (_odf_text(p) for p in cell.iter(TEXT + "p")) if t)
            for cell in row.findall(TABLE + "table-cell")
        ])
    return pipe_table(rows)


def _odf_list(lst, depth, lines):
    for item in lst:
        if _local(item.tag) not in ("list-item", "list-header"):
            continue
        for child in item:
            name = _local(child.tag)
            if name == "list":
                _odf_list(child, depth + 1, lines)
            elif name in ("p", "h"):
                text = _odf_text(child)
                if text:
                    lines.append("  " * depth + "- " + text)


def _odf_blocks(container, items, headings=True):
    """Append ("heading"|"text", payload) items from ODF block content."""
    for child in container:
        name = _local(child.tag)
        if name in ODF_SKIP:
            continue
        if name == "h" and headings:
            text = _odf_text(child)
            level = child.get(TEXT + "outline-level") or "1"
            level = int(level) if level.isdigit() else 1
            if text:
                items.append(
                    ("heading", " ".join(text.split())) if level <= 2
                    else ("text", text)
                )
        elif name in ("p", "h"):
            text = _odf_text(child)
            if text:
                items.append(("text", text))
        elif name == "list":
            lines = []
            _odf_list(child, 0, lines)
            items.extend(("text", line) for line in lines)
        elif name == "table":
            table = _odf_table(child)
            if table:
                items.append(("text", table))
        elif name in ("section", "text-box", "g", "frame", "notes"):
            _odf_blocks(child, items, headings)
        elif name == "image":
            continue


def _odf_frames(container, out, notes=False):
    for child in container:
        name = _local(child.tag)
        if name == "g":
            _odf_frames(child, out, notes)
        elif name == "notes" and not notes:
            continue
        elif name == "frame":
            cls = child.get(PRES + "class") or ""
            if cls in ODF_CHROME_CLASSES:
                continue
            items = []
            _odf_blocks(child, items, headings=False)
            texts = [payload for _, payload in items]
            if cls == "title" and not notes and not out["title"]:
                out["title"] = " ".join(" ".join(texts).split()) or None
                continue
            marker = _odf_image(child).strip()
            if marker:
                out["lines"].append(marker)
            out["lines"].extend(texts)


def _parse_odf(zf, path: Path, fmt: str):
    root = _xml(zf, MAIN_PART[fmt], path)
    props = _properties(_optional_xml(zf, "meta.xml", path))
    body = root.find(f"{OFFICE}body")
    if fmt == "odt":
        items = []
        text_el = body.find(OFFICE + "text") if body is not None else None
        if text_el is not None:
            _odf_blocks(text_el, items)
        return _sections(items), props, props["title"], {}
    sections, flags = [], {}
    pres = body.find(OFFICE + "presentation") if body is not None else None
    pages = pres.findall(DRAW + "page") if pres is not None else []
    for number, page in enumerate(pages, start=1):
        out = {"title": None, "lines": []}
        _odf_frames(page, out)
        notes = {"title": None, "lines": []}
        notes_el = page.find(PRES + "notes")
        if notes_el is not None:
            _odf_frames(notes_el, notes, notes=True)
        body_text = "\n".join(out["lines"])
        if notes["lines"]:
            body_text += ("\n\n" if body_text else "") + "Notes:\n" + "\n".join(
                notes["lines"]
            )
        sections.append((out["title"] or f"Slide {number}", body_text))
        flags[len(sections) - 1] = {"slide": number}
    return sections, props, props["title"], flags


# --- entry point ------------------------------------------------------------


def _open(path: Path, fmt: str):
    try:
        zf = zipfile.ZipFile(path)
    except (zipfile.BadZipFile, OSError) as err:
        raise ExtractError(
            f"{path} is not a valid .{fmt} file (cannot read as zip: {err}).\n"
            "It may be corrupted, password-protected, or a different format "
            "- re-save it from its editor and retry."
        ) from err
    if MAIN_PART[fmt] not in zf.namelist():
        zf.close()
        raise ExtractError(
            f"{path} has no {MAIN_PART[fmt]} - not a valid .{fmt} file.\n"
            "Re-save it from its editor and retry."
        )
    return zf


def parse(source: str):
    if re.match(r"https?://", source):
        raise ExtractError(
            f"Unsupported document URL: {source}\n"
            "Documents are read from local files - download the file and "
            "pass its path."
        )
    path = Path(source).expanduser()
    suffix = path.suffix.lower()
    if suffix in LEGACY_FORMATS:
        raise ExtractError(
            f"Legacy {suffix} files are not supported: {path.name}\n"
            f"Save it as {LEGACY_FORMATS[suffix]} (File > Save As) and retry."
        )
    fmt = suffix.lstrip(".")
    if fmt not in MAIN_PART:
        raise ExtractError(
            f"Unsupported document format: {path.name}\n"
            "Supported: .docx, .pptx, .odt, .odp."
        )
    if not path.is_file():
        raise ExtractError(f"Document not found: {path}")
    with _open(path, fmt) as zf:
        if fmt == "docx":
            sections, props, title, flags = _parse_docx(zf, path)
        elif fmt == "pptx":
            sections, props, title, flags = _parse_pptx(zf, path)
        else:
            sections, props, title, flags = _parse_odf(zf, path, fmt)
    if not any(
        body.strip()
        or not re.fullmatch(r"Full text|Introduction|Slide \d+", seg_title)
        for seg_title, body in sections
    ):
        raise ExtractError(
            f"{path} has no extractable text.\n"
            "Image-only documents and scans need OCR, which is not "
            "supported - export the text and retry."
        )
    chunks, segments, offset = [], [], 0
    # Headings and slide titles repeat ("Summary", "Questions?"); the
    # key keeps each segment distinct for refresh diffs.
    keys = utils.unique_keys(seg_title for seg_title, _ in sections)
    for index, (seg_title, body) in enumerate(sections):
        chunk = f"=== {seg_title} ===\n{body}\n\n"
        segment = {
            "title": seg_title, "start_s": None, "pages": None,
            "offset": offset, "key": keys[index],
        }
        segment.update(flags.get(index, {}))
        segments.append(segment)
        chunks.append(chunk)
        offset += len(chunk)
    full_text = "".join(chunks)
    words = len(full_text.split())
    metadata = {
        "source_type": "document",
        "format": fmt,
        "title": title or re.sub(r"[_-]+", " ", path.stem).strip() or "Untitled document",
        "author": props["author"],
        "date": props["date"],
        "origin": source,
        "language": props["language"],
        "words": words,
        "est_tokens": utils.estimate_tokens(words),
        "segments": segments,
    }
    if fmt in ("pptx", "odp"):
        metadata["slide_count"] = len(segments)
    return full_text, metadata
