"""Tests for the Word/PowerPoint/OpenDocument parser. Fixtures are
hand-written OOXML/ODF zips built in tmp_path - no third-party libraries."""
import json
import zipfile

import pytest

import extract
from extractor import utils
from extractor.parsers import document
from extractor.utils import ExtractError

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
CORE = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties
  xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
  xmlns:dc="http://purl.org/dc/elements/1.1/"
  xmlns:dcterms="http://purl.org/dc/terms/"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
<dc:title>{title}</dc:title><dc:creator>{creator}</dc:creator>
<dc:language>en-US</dc:language>
<dcterms:created xsi:type="dcterms:W3CDTF">2026-03-14T09:30:00Z</dcterms:created>
</cp:coreProperties>"""


def _zip(path, files):
    with zipfile.ZipFile(path, "w") as zf:
        for name, data in files.items():
            zf.writestr(name, data)
    return path


# --- DOCX -------------------------------------------------------------------


def _p(text, style=None, num=None, outline=None, extra=""):
    ppr = ""
    if style or num is not None or outline is not None:
        ppr = "<w:pPr>"
        if style:
            ppr += f'<w:pStyle w:val="{style}"/>'
        if num is not None:
            ppr += f'<w:numPr><w:ilvl w:val="{num}"/><w:numId w:val="1"/></w:numPr>'
        if outline is not None:
            ppr += f'<w:outlineLvl w:val="{outline}"/>'
        ppr += "</w:pPr>"
    return f"<w:p>{ppr}<w:r><w:t xml:space=\"preserve\">{text}</w:t></w:r>{extra}</w:p>"


def _cell(text):
    return f"<w:tc>{_p(text)}</w:tc>"


TABLE = (
    "<w:tbl><w:tr>" + _cell("Metric") + _cell("Value") + "</w:tr>"
    "<w:tr>" + _cell("Latency") + _cell("12 ms | p95") + "</w:tr></w:tbl>"
)

IMAGE = (
    "<w:p><w:r><w:drawing><wp:inline "
    'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing">'
    '<wp:docPr id="1" name="Picture 1" descr="Architecture diagram"/>'
    "</wp:inline></w:drawing></w:r></w:p>"
)

FOOTNOTE_AND_COMMENT = (
    "<w:p><w:commentRangeStart w:id=\"0\"/><w:r><w:t>Body with refs</w:t></w:r>"
    "<w:r><w:footnoteReference w:id=\"1\"/></w:r>"
    "<w:commentRangeEnd w:id=\"0\"/>"
    "<w:r><w:commentReference w:id=\"0\"/></w:r></w:p>"
)

STYLES = f"""<?xml version="1.0" encoding="UTF-8"?>
<w:styles xmlns:w="{W_NS}">
<w:style w:type="paragraph" w:styleId="Nadpis1"><w:name w:val="heading 1"/></w:style>
<w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="heading 2"/></w:style>
<w:style w:type="paragraph" w:styleId="Heading3"><w:name w:val="heading 3"/></w:style>
<w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title"/></w:style>
</w:styles>"""


def _docx(tmp_path, body, name="report.docx", core=True, styles=True):
    files = {
        "[Content_Types].xml": "<Types/>",
        "word/document.xml": (
            f'<?xml version="1.0" encoding="UTF-8"?>'
            f'<w:document xmlns:w="{W_NS}"><w:body>{body}'
            "<w:sectPr/></w:body></w:document>"
        ),
    }
    if core:
        files["docProps/core.xml"] = CORE.format(
            title="Quarterly Review", creator="Ada Lovelace"
        )
    if styles:
        files["word/styles.xml"] = STYLES
    files["word/footnotes.xml"] = (
        f'<w:footnotes xmlns:w="{W_NS}"><w:footnote w:id="1">'
        "<w:p><w:r><w:t>FOOTNOTE TEXT</w:t></w:r></w:p></w:footnote></w:footnotes>"
    )
    return _zip(tmp_path / name, files)


DOCX_BODY = (
    _p("Quarterly Review", style="Title")
    + _p("Lead-in paragraph before any heading.")
    + _p("Results", style="Nadpis1")
    + _p("We shipped three things.")
    + _p("first bullet", num=0)
    + _p("nested bullet", num=1)
    + TABLE
    + IMAGE
    + _p("Details", style="Heading3")
    + FOOTNOTE_AND_COMMENT
    + _p("Next Steps", style="Heading2")
    + _p("Hire two engineers.")
    + _p("Appendix", outline=0)
    + _p("Raw numbers.")
)


def test_docx_metadata_from_core_xml(tmp_path):
    path = _docx(tmp_path, DOCX_BODY)
    _, meta = document.parse(str(path))
    assert meta["source_type"] == "document"
    assert meta["format"] == "docx"
    assert meta["title"] == "Quarterly Review"
    assert meta["author"] == "Ada Lovelace"
    assert meta["date"] == "2026-03-14"
    assert meta["language"] == "en-US"
    assert meta["origin"] == str(path)
    assert meta["words"] > 0
    assert meta["est_tokens"] == utils.estimate_tokens(meta["words"])


def test_docx_headings_level_1_and_2_are_segment_boundaries(tmp_path):
    full_text, meta = document.parse(str(_docx(tmp_path, DOCX_BODY)))
    titles = [seg["title"] for seg in meta["segments"]]
    # Text before the first heading becomes an Introduction segment; the
    # Title-style paragraph is the document title, not body text. Outline
    # level 0 on a plain paragraph counts as a level-1 heading; Heading 3
    # stays inside its section.
    assert titles == ["Introduction", "Results", "Next Steps", "Appendix"]
    for seg in meta["segments"]:
        assert full_text[seg["offset"]:].startswith(f"=== {seg['title']} ===")
        assert seg["start_s"] is None and seg["pages"] is None
    assert "Details" in full_text


def test_docx_lists_tables_images(tmp_path):
    full_text, _ = document.parse(str(_docx(tmp_path, DOCX_BODY)))
    assert "\n- first bullet\n" in full_text
    assert "\n  - nested bullet\n" in full_text
    assert "| Metric | Value |\n| --- | --- |\n| Latency | 12 ms \\| p95 |" in full_text
    assert "[image: Architecture diagram]" in full_text


def test_docx_ignores_footnotes_and_comments(tmp_path):
    full_text, _ = document.parse(str(_docx(tmp_path, DOCX_BODY)))
    assert "Body with refs" in full_text
    assert "FOOTNOTE TEXT" not in full_text


def test_docx_list_styles_without_numbering_keep_their_level(tmp_path):
    body = _p("top", style="ListBullet") + _p("inner", style="ListBullet2")
    styles = STYLES.replace(
        "</w:styles>",
        '<w:style w:type="paragraph" w:styleId="ListBullet"><w:name w:val="List Bullet"/></w:style>'
        '<w:style w:type="paragraph" w:styleId="ListBullet2"><w:name w:val="List Bullet 2"/></w:style>'
        "</w:styles>",
    )
    path = _docx(tmp_path, body, styles=False)
    with zipfile.ZipFile(path, "a") as zf:
        zf.writestr("word/styles.xml", styles)
    full_text, _ = document.parse(str(path))
    assert "- top\n  - inner" in full_text


def test_docx_tracked_deletions_dropped_insertions_and_links_kept(tmp_path):
    body = (
        "<w:p><w:r><w:t>Keep </w:t></w:r>"
        "<w:del><w:r><w:delText>gone </w:delText></w:r></w:del>"
        "<w:ins><w:r><w:t>added </w:t></w:r></w:ins>"
        "<w:hyperlink><w:r><w:t>linked</w:t></w:r></w:hyperlink>"
        "<w:r><w:tab/><w:t>tabbed</w:t><w:br/><w:t>broken</w:t></w:r></w:p>"
    )
    full_text, _ = document.parse(str(_docx(tmp_path, body)))
    assert "Keep added linked tabbed\nbroken" in full_text
    assert "gone" not in full_text


def test_docx_alternate_content_not_duplicated(tmp_path):
    body = (
        '<w:p xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006">'
        "<w:r><mc:AlternateContent>"
        "<mc:Choice><w:t>textbox once</w:t></mc:Choice>"
        "<mc:Fallback><w:t>textbox once</w:t></mc:Fallback>"
        "</mc:AlternateContent></w:r></w:p>"
    )
    full_text, _ = document.parse(str(_docx(tmp_path, body)))
    assert full_text.count("textbox once") == 1


def test_docx_without_core_or_headings_falls_back(tmp_path):
    path = _docx(
        tmp_path, _p("Only a paragraph."), name="my_notes-v2.docx",
        core=False, styles=False,
    )
    full_text, meta = document.parse(str(path))
    assert meta["title"] == "my notes v2"
    assert meta["author"] is None and meta["date"] is None
    assert [s["title"] for s in meta["segments"]] == ["Full text"]
    assert "Only a paragraph." in full_text


def test_docx_builtin_heading_ids_work_without_styles_xml(tmp_path):
    body = _p("Intro", style="Heading1") + _p("text one") + _p(
        "Second", style="heading2"
    ) + _p("text two")
    _, meta = document.parse(str(_docx(tmp_path, body, styles=False)))
    assert [s["title"] for s in meta["segments"]] == ["Intro", "Second"]


# --- PPTX -------------------------------------------------------------------

P_NS = (
    'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
    'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
    'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"'
)
REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
SLIDE_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide"
NOTES_REL = (
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/notesSlide"
)


def _sp(paras, ph=None):
    ph_xml = f'<p:ph type="{ph}"/>' if ph == "title" else (
        '<p:ph idx="1"/>' if ph == "body" else (
            f'<p:ph type="{ph}"/>' if ph else ""
        )
    )
    body = "".join(
        (f'<a:p><a:pPr lvl="{lvl}"/><a:r><a:t>{text}</a:t></a:r></a:p>')
        for lvl, text in paras
    )
    return (
        f"<p:sp><p:nvSpPr><p:cNvPr id=\"2\" name=\"s\"/><p:cNvSpPr/>"
        f"<p:nvPr>{ph_xml}</p:nvPr></p:nvSpPr>"
        f"<p:txBody><a:bodyPr/>{body}</p:txBody></p:sp>"
    )


def _slide(shapes, hidden=False):
    show = ' show="0"' if hidden else ""
    return (
        f'<?xml version="1.0"?><p:sld {P_NS}{show}><p:cSld><p:spTree>'
        f"{shapes}</p:spTree></p:cSld></p:sld>"
    )


PPT_TABLE = (
    "<p:graphicFrame><a:graphic><a:graphicData><a:tbl>"
    "<a:tr><a:tc><a:txBody><a:p><a:r><a:t>Plan</a:t></a:r></a:p></a:txBody></a:tc>"
    "<a:tc><a:txBody><a:p><a:r><a:t>Price</a:t></a:r></a:p></a:txBody></a:tc></a:tr>"
    "<a:tr><a:tc><a:txBody><a:p><a:r><a:t>Pro</a:t></a:r></a:p></a:txBody></a:tc>"
    "<a:tc><a:txBody><a:p><a:r><a:t>$20</a:t></a:r></a:p></a:txBody></a:tc></a:tr>"
    "</a:tbl></a:graphicData></a:graphic></p:graphicFrame>"
)
PPT_PIC = (
    '<p:pic><p:nvPicPr><p:cNvPr id="5" name="Picture 4" descr="Revenue chart"/>'
    "</p:nvPicPr></p:pic>"
)


def _pptx(tmp_path, name="deck.pptx"):
    # Presentation order (sldIdLst) differs from file numbering on purpose.
    slides = {
        "slide1.xml": _slide(
            _sp([(0, "Pricing")], ph="title")
            + _sp([(0, "Three tiers"), (1, "Pro is the default")], ph="body")
            + PPT_TABLE
        ),
        "slide2.xml": _slide(
            _sp([(0, "Welcome")], ph="ctrTitle")
            + _sp([(0, "A subtitle line")], ph="subTitle")
        ),
        "slide3.xml": _slide(
            _sp([(0, "Free-floating text box")]) + PPT_PIC
            + "<p:grpSp>" + _sp([(0, "Grouped text")]) + "</p:grpSp>"
        ),
    }
    notes = (
        f'<?xml version="1.0"?><p:notes {P_NS}><p:cSld><p:spTree>'
        + _sp([(0, "slide image")], ph="sldImg")
        + _sp([(0, "Say the margin is 40%."), (0, "Pause for questions.")], ph="body")
        + _sp([(0, "3")], ph="sldNum")
        + "</p:spTree></p:cSld></p:notes>"
    )
    files = {
        "[Content_Types].xml": "<Types/>",
        "docProps/core.xml": CORE.format(title="Launch Deck", creator="Grace Hopper"),
        "ppt/presentation.xml": (
            f'<?xml version="1.0"?><p:presentation {P_NS}><p:sldIdLst>'
            '<p:sldId id="256" r:id="rId7"/>'
            '<p:sldId id="257" r:id="rId8"/>'
            '<p:sldId id="258" r:id="rId9"/>'
            "</p:sldIdLst></p:presentation>"
        ),
        "ppt/_rels/presentation.xml.rels": (
            f'<?xml version="1.0"?><Relationships xmlns="{REL_NS}">'
            f'<Relationship Id="rId7" Type="{SLIDE_REL}" Target="slides/slide2.xml"/>'
            f'<Relationship Id="rId8" Type="{SLIDE_REL}" Target="slides/slide1.xml"/>'
            f'<Relationship Id="rId9" Type="{SLIDE_REL}" Target="/ppt/slides/slide3.xml"/>'
            "</Relationships>"
        ),
        "ppt/slides/_rels/slide1.xml.rels": (
            f'<?xml version="1.0"?><Relationships xmlns="{REL_NS}">'
            f'<Relationship Id="rId2" Type="{NOTES_REL}" '
            'Target="../notesSlides/notesSlide1.xml"/></Relationships>'
        ),
        "ppt/notesSlides/notesSlide1.xml": notes,
    }
    for name_, xml in slides.items():
        files[f"ppt/slides/{name_}"] = xml
    return _zip(tmp_path / name, files)


def test_pptx_one_segment_per_slide_in_presentation_order(tmp_path):
    full_text, meta = document.parse(str(_pptx(tmp_path)))
    assert meta["source_type"] == "document"
    assert meta["format"] == "pptx"
    assert meta["title"] == "Launch Deck"
    assert meta["author"] == "Grace Hopper"
    assert meta["slide_count"] == 3
    assert [(s["slide"], s["title"]) for s in meta["segments"]] == [
        (1, "Welcome"), (2, "Pricing"), (3, "Slide 3"),
    ]
    for seg in meta["segments"]:
        assert full_text[seg["offset"]:].startswith(f"=== {seg['title']} ===")


def test_pptx_bullets_tables_pictures_and_notes(tmp_path):
    full_text, meta = document.parse(str(_pptx(tmp_path)))
    pricing = full_text[meta["segments"][1]["offset"]:meta["segments"][2]["offset"]]
    assert "- Three tiers\n  - Pro is the default" in pricing
    assert "| Plan | Price |\n| --- | --- |\n| Pro | $20 |" in pricing
    assert "Notes:\nSay the margin is 40%.\nPause for questions." in pricing
    assert "slide image" not in full_text
    welcome = full_text[:meta["segments"][1]["offset"]]
    # A subtitle is plain text, not a bullet; the title is not repeated.
    assert "\nA subtitle line\n" in welcome
    assert welcome.count("Welcome") == 1
    third = full_text[meta["segments"][2]["offset"]:]
    assert "Free-floating text box" in third
    assert "Grouped text" in third
    assert "[image: Revenue chart]" in third
    assert "Notes:" not in third


def test_pptx_hidden_slide_flagged(tmp_path):
    path = _pptx(tmp_path)
    with zipfile.ZipFile(path) as zf:
        files = {n: zf.read(n) for n in zf.namelist()}
    files["ppt/slides/slide3.xml"] = _slide(_sp([(0, "Backup")], ph="title"), hidden=True)
    _zip(path, files)
    _, meta = document.parse(str(path))
    assert meta["segments"][2].get("hidden") is True
    assert "hidden" not in meta["segments"][0]


# --- ODF --------------------------------------------------------------------

ODF_NS = (
    'xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" '
    'xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0" '
    'xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0" '
    'xmlns:draw="urn:oasis:names:tc:opendocument:xmlns:drawing:1.0" '
    'xmlns:svg="urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0" '
    'xmlns:presentation="urn:oasis:names:tc:opendocument:xmlns:presentation:1.0"'
)
ODF_META = (
    '<?xml version="1.0"?><office:document-meta '
    'xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" '
    'xmlns:dc="http://purl.org/dc/elements/1.1/" '
    'xmlns:meta="urn:oasis:names:tc:opendocument:xmlns:meta:1.0">'
    "<office:meta><dc:title>Open Doc</dc:title>"
    "<meta:initial-creator>Linus</meta:initial-creator>"
    "<meta:creation-date>2025-12-01T10:00:00</meta:creation-date>"
    "</office:meta></office:document-meta>"
)


def test_odt_headings_lists_tables(tmp_path):
    content = (
        f'<?xml version="1.0"?><office:document-content {ODF_NS}>'
        "<office:body><office:text>"
        '<text:h text:outline-level="1">Overview</text:h>'
        "<text:p>Hello <text:span>world</text:span>.</text:p>"
        "<text:list><text:list-item><text:p>alpha</text:p>"
        "<text:list><text:list-item><text:p>beta</text:p></text:list-item></text:list>"
        "</text:list-item></text:list>"
        "<table:table><table:table-row><table:table-cell><text:p>k</text:p></table:table-cell>"
        "<table:table-cell><text:p>v</text:p></table:table-cell></table:table-row></table:table>"
        '<text:h text:outline-level="2">Details</text:h>'
        "<text:p>More<text:note><text:note-body><text:p>NOTE</text:p></text:note-body></text:note></text:p>"
        '<text:h text:outline-level="3">Deep</text:h>'
        "</office:text></office:body></office:document-content>"
    )
    path = _zip(tmp_path / "doc.odt", {"content.xml": content, "meta.xml": ODF_META})
    full_text, meta = document.parse(str(path))
    assert meta["format"] == "odt"
    assert meta["title"] == "Open Doc"
    assert meta["author"] == "Linus"
    assert meta["date"] == "2025-12-01"
    assert [s["title"] for s in meta["segments"]] == ["Overview", "Details"]
    assert "Hello world." in full_text
    assert "\n- alpha\n  - beta\n" in full_text
    assert "| k | v |" in full_text
    assert "NOTE" not in full_text
    assert "Deep" in full_text


def test_odp_slides_titles_and_notes(tmp_path):
    content = (
        f'<?xml version="1.0"?><office:document-content {ODF_NS}>'
        "<office:body><office:presentation>"
        '<draw:page draw:name="p1">'
        '<draw:frame presentation:class="title"><draw:text-box><text:p>Hello Deck</text:p></draw:text-box></draw:frame>'
        '<draw:frame presentation:class="outline"><draw:text-box>'
        "<text:list><text:list-item><text:p>point one</text:p></text:list-item></text:list>"
        "</draw:text-box></draw:frame>"
        "<presentation:notes><draw:frame presentation:class=\"notes\"><draw:text-box>"
        "<text:p>Speak slowly.</text:p></draw:text-box></draw:frame></presentation:notes>"
        "</draw:page>"
        '<draw:page draw:name="p2"><draw:frame><draw:text-box><text:p>untitled body</text:p>'
        "</draw:text-box></draw:frame></draw:page>"
        "</office:presentation></office:body></office:document-content>"
    )
    path = _zip(tmp_path / "talk.odp", {"content.xml": content})
    full_text, meta = document.parse(str(path))
    assert meta["format"] == "odp"
    assert meta["title"] == "talk"
    assert [(s["slide"], s["title"]) for s in meta["segments"]] == [
        (1, "Hello Deck"), (2, "Slide 2"),
    ]
    assert "- point one" in full_text
    assert "Notes:\nSpeak slowly." in full_text


# --- errors and detection ---------------------------------------------------


def test_missing_and_corrupt_files(tmp_path):
    with pytest.raises(ExtractError, match="not found"):
        document.parse(str(tmp_path / "nope.docx"))
    bad = tmp_path / "bad.pptx"
    bad.write_bytes(b"not a zip")
    with pytest.raises(ExtractError, match="not a valid"):
        document.parse(str(bad))
    empty = _zip(tmp_path / "empty.docx", {"[Content_Types].xml": "<Types/>"})
    with pytest.raises(ExtractError, match="word/document.xml"):
        document.parse(str(empty))


def test_legacy_binary_formats_get_a_conversion_hint(tmp_path):
    legacy = tmp_path / "old.doc"
    legacy.write_bytes(b"\xd0\xcf\x11\xe0")
    with pytest.raises(ExtractError, match="Save it as .docx"):
        document.parse(str(legacy))


def test_url_rejected():
    with pytest.raises(ExtractError, match="local files"):
        document.parse("https://example.com/deck.pptx")


@pytest.mark.parametrize(
    "source", ["report.docx", "~/Deck.PPTX", "notes.odt", "talk.odp"]
)
def test_detect_document(source):
    assert utils.detect_source(source) == "document"


def test_cli_writes_outputs(tmp_path, capsys):
    path = _docx(tmp_path, DOCX_BODY)
    work = tmp_path / "work"
    assert extract.main([str(path), "--work-dir", str(work)]) == 0
    meta = json.loads((work / "metadata.json").read_text())
    assert meta["source_type"] == "document"
    assert (work / "full_text.txt").read_text().startswith("=== Introduction ===")
    summary = json.loads(capsys.readouterr().out)
    assert summary["source_type"] == "document"
