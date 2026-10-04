import zipfile

import pytest

from extractor.parsers import book
from extractor.utils import ExtractError

# (filename, ncx title, h1 heading or None, body html)
CHAPTERS = [
    (
        "ch1.xhtml",
        "The Beginning",
        "Chapter One",
        "<p>Cats &amp; dogs live together in peace.</p>"
        "<p>It was a <b>bold</b> start &mdash; truly.</p>",
    ),
    (
        "ch2.xhtml",
        "The Middle",
        "Chapter Two",
        "<p>The plot thickens with <i>style</i>.</p>",
    ),
    (
        "ch3.xhtml",
        "The End",
        None,
        "<p>They all lived happily ever after.</p>",
    ),
]

CONTAINER_XML = """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>
"""

NAV_XHTML = """<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head><title>Contents</title></head>
<body>
<nav epub:type="toc">
<ol>
<li><a href="ch1.xhtml">Part A</a></li>
<li><a href="ch2.xhtml">Part B</a></li>
<li><a href="ch3.xhtml">Part C</a></li>
</ol>
</nav>
</body>
</html>
"""


def chapter_xhtml(n, h1_title, body):
    h1 = f"<h1>{h1_title}</h1>" if h1_title else ""
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<html xmlns="http://www.w3.org/1999/xhtml">'
        f"<head><title>Doc {n}</title></head>"
        f"<body>{h1}{body}</body></html>"
    )


def opf_xml(
    *,
    with_ncx=True,
    with_nav=False,
    empty_spine=False,
    extra_items="",
    extra_itemrefs="",
):
    items = "".join(
        f'<item id="ch{i}" href="{name}" media-type="application/xhtml+xml"/>'
        for i, (name, _, _, _) in enumerate(CHAPTERS, start=1)
    )
    if with_ncx:
        items += '<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>'
    if with_nav:
        items += (
            '<item id="nav" href="nav.xhtml" '
            'media-type="application/xhtml+xml" properties="nav"/>'
        )
    items += extra_items
    itemrefs = (
        ""
        if empty_spine
        else "".join(
            f'<itemref idref="ch{i}"/>' for i in range(1, len(CHAPTERS) + 1)
        )
        + extra_itemrefs
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<package xmlns="http://www.idpf.org/2007/opf" version="2.0">'
        '<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">'
        "<dc:title>Deep Focus</dc:title>"
        "<dc:creator>Jane Q. Author</dc:creator>"
        "<dc:language>en</dc:language>"
        "</metadata>"
        f"<manifest>{items}</manifest>"
        f'<spine toc="ncx">{itemrefs}</spine>'
        "</package>"
    )


def ncx_xml():
    points = "".join(
        f'<navPoint id="np{i}" playOrder="{i}">'
        f"<navLabel><text>{title}</text></navLabel>"
        f'<content src="{name}"/></navPoint>'
        for i, (name, title, _, _) in enumerate(CHAPTERS, start=1)
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">'
        f"<navMap>{points}</navMap></ncx>"
    )


def make_epub(
    tmp_path,
    *,
    with_container=True,
    with_ncx=True,
    with_nav=False,
    empty_spine=False,
    ncx_content=None,
    nav_content=None,
    extra_items="",
    extra_itemrefs="",
    name="book.epub",
):
    path = tmp_path / name
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("mimetype", "application/epub+zip")
        if with_container:
            zf.writestr("META-INF/container.xml", CONTAINER_XML)
        zf.writestr(
            "OEBPS/content.opf",
            opf_xml(
                with_ncx=with_ncx,
                with_nav=with_nav,
                empty_spine=empty_spine,
                extra_items=extra_items,
                extra_itemrefs=extra_itemrefs,
            ),
        )
        if with_ncx:
            zf.writestr(
                "OEBPS/toc.ncx",
                ncx_xml() if ncx_content is None else ncx_content,
            )
        if with_nav:
            zf.writestr(
                "OEBPS/nav.xhtml",
                NAV_XHTML if nav_content is None else nav_content,
            )
        for i, (fname, _, h1_title, body) in enumerate(CHAPTERS, start=1):
            zf.writestr(f"OEBPS/{fname}", chapter_xhtml(i, h1_title, body))
    return path


def test_parse_epub_metadata_and_chapter_segments(tmp_path):
    path = make_epub(tmp_path)
    full_text, meta = book.parse(str(path))
    assert meta["source_type"] == "book"
    assert meta["title"] == "Deep Focus"
    assert meta["author"] == "Jane Q. Author"
    assert meta["language"] == "en"
    assert meta["words"] == len(full_text.split())
    assert meta["est_tokens"] > 0
    titles = [s["title"] for s in meta["segments"]]
    assert titles == ["The Beginning", "The Middle", "The End"]
    assert all(s["start_s"] is None for s in meta["segments"])
    assert all(s["pages"] is None for s in meta["segments"])
    offsets = [s["offset"] for s in meta["segments"]]
    assert offsets == sorted(offsets)
    assert len(set(offsets)) == len(offsets)
    for seg in meta["segments"]:
        first_line = full_text[seg["offset"]:].splitlines()[0]
        assert seg["title"] in first_line
    middle = full_text[offsets[1]:offsets[2]]
    assert "The plot thickens with style." in middle


def test_parse_epub_strips_tags_and_decodes_entities(tmp_path):
    path = make_epub(tmp_path)
    full_text, _ = book.parse(str(path))
    assert "Cats & dogs live together in peace." in full_text
    assert "It was a bold start — truly." in full_text
    assert "&amp;" not in full_text
    assert "<p>" not in full_text
    assert "<b>" not in full_text


def test_parse_epub_falls_back_to_h1_then_title_without_ncx(tmp_path):
    path = make_epub(tmp_path, with_ncx=False)
    _, meta = book.parse(str(path))
    titles = [s["title"] for s in meta["segments"]]
    assert titles == ["Chapter One", "Chapter Two", "Doc 3"]


def test_parse_epub_uses_nav_toc_when_no_ncx(tmp_path):
    path = make_epub(tmp_path, with_ncx=False, with_nav=True)
    _, meta = book.parse(str(path))
    titles = [s["title"] for s in meta["segments"]]
    assert titles == ["Part A", "Part B", "Part C"]


def test_parse_epub_malformed_ncx_falls_back_to_headings(tmp_path):
    # &nbsp; is undefined in XML - common in hand-edited or converted books.
    broken = ncx_xml().replace("The Beginning", "The&nbsp;Beginning")
    path = make_epub(tmp_path, ncx_content=broken)
    _, meta = book.parse(str(path))
    titles = [s["title"] for s in meta["segments"]]
    assert titles == ["Chapter One", "Chapter Two", "Doc 3"]


def test_parse_epub_malformed_ncx_uses_nav_when_present(tmp_path):
    broken = ncx_xml().replace("The Beginning", "The&nbsp;Beginning")
    path = make_epub(tmp_path, ncx_content=broken, with_nav=True)
    _, meta = book.parse(str(path))
    titles = [s["title"] for s in meta["segments"]]
    assert titles == ["Part A", "Part B", "Part C"]


def test_parse_epub_nav_toc_with_multiple_epub_types(tmp_path):
    # epub:type is a space-separated property list per the EPUB spec.
    nav = NAV_XHTML.replace('epub:type="toc"', 'epub:type="toc landmarks"')
    path = make_epub(tmp_path, with_ncx=False, with_nav=True, nav_content=nav)
    _, meta = book.parse(str(path))
    titles = [s["title"] for s in meta["segments"]]
    assert titles == ["Part A", "Part B", "Part C"]


def test_parse_epub_untyped_nav_is_not_a_toc(tmp_path):
    # A <nav> without epub:type="toc" must not override heading fallbacks.
    nav = NAV_XHTML.replace(' epub:type="toc"', "")
    path = make_epub(tmp_path, with_ncx=False, with_nav=True, nav_content=nav)
    _, meta = book.parse(str(path))
    titles = [s["title"] for s in meta["segments"]]
    assert titles == ["Chapter One", "Chapter Two", "Doc 3"]


def test_parse_epub_warns_about_missing_spine_chapters(tmp_path, capsys):
    path = make_epub(
        tmp_path,
        extra_items=(
            '<item id="ghost" href="missing.xhtml" '
            'media-type="application/xhtml+xml"/>'
        ),
        extra_itemrefs='<itemref idref="ghost"/><itemref idref="nosuchid"/>',
    )
    _, meta = book.parse(str(path))
    titles = [s["title"] for s in meta["segments"]]
    assert titles == ["The Beginning", "The Middle", "The End"]
    err = capsys.readouterr().err
    assert "missing.xhtml" in err
    assert "nosuchid" in err
    assert "incomplete" in err


def test_chapter_text_separates_adjacent_table_cells():
    text, _, _ = book._chapter_text(
        "<html><body><table><tr><td>Alpha</td><td>Beta</td></tr>"
        "<tr><th>Gamma</th><th>Delta</th></tr></table></body></html>"
    )
    words = text.split()
    assert "AlphaBeta" not in words
    assert "GammaDelta" not in words
    assert {"Alpha", "Beta", "Gamma", "Delta"} <= set(words)


def test_chapter_text_h1_with_br_keeps_word_break():
    _, h1, _ = book._chapter_text(
        "<html><body><h1>Line<br/>Two</h1><p>Body.</p></body></html>"
    )
    assert h1 == "Line Two"


def test_parse_epub_missing_container_errors(tmp_path):
    path = make_epub(tmp_path, with_container=False)
    with pytest.raises(ExtractError, match="container.xml"):
        book.parse(str(path))


def test_parse_epub_empty_spine_errors(tmp_path):
    path = make_epub(tmp_path, empty_spine=True)
    with pytest.raises(ExtractError, match="spine"):
        book.parse(str(path))


def test_parse_epub_not_a_zip_errors(tmp_path):
    path = tmp_path / "fake.epub"
    path.write_bytes(b"this is not a zip archive")
    with pytest.raises(ExtractError, match="not a valid EPUB"):
        book.parse(str(path))


def test_parse_missing_file_errors():
    with pytest.raises(ExtractError, match="Book not found"):
        book.parse("/nonexistent/nope.epub")


PDF_FILLER = """The quick brown fox jumps over the lazy dog while narrating
a long story about focus, craft, and the slow accumulation of skill
across many patient years of deliberate practice and honest reflection
on the nature of work done well and the habits that sustain it daily.
"""


def make_pdf(tmp_path, pages, toc=None, doc_meta=None, name="book.pdf"):
    fitz = pytest.importorskip("fitz")
    path = tmp_path / name
    doc = fitz.open()
    for text in pages:
        page = doc.new_page()
        page.insert_text((72, 72), text)
    if doc_meta:
        doc.set_metadata(doc_meta)
    if toc:
        doc.set_toc(toc)
    doc.save(path)
    doc.close()
    return path


def test_parse_pdf_book_chapters_from_outline(tmp_path):
    path = make_pdf(
        tmp_path,
        [PDF_FILLER, PDF_FILLER, PDF_FILLER],
        toc=[
            [1, "Chapter One", 1],
            [2, "A Nested Section", 1],
            [1, "Chapter Two", 2],
            [1, "Chapter Three", 3],
        ],
        doc_meta={"title": "PDF Book", "author": "Ada Writer"},
    )
    full_text, meta = book.parse(str(path))
    assert meta["source_type"] == "book"
    assert meta["title"] == "PDF Book"
    assert meta["author"] == "Ada Writer"
    assert meta["page_count"] == 3
    titles = [s["title"] for s in meta["segments"]]
    assert titles == ["Chapter One", "Chapter Two", "Chapter Three"]
    assert [s["pages"] for s in meta["segments"]] == [1, 2, 3]
    assert all(s["start_s"] is None for s in meta["segments"])
    offsets = [s["offset"] for s in meta["segments"]]
    assert offsets[0] == 0
    assert offsets == sorted(offsets)
    assert len(set(offsets)) == len(offsets)


def test_parse_pdf_book_outline_skips_unresolved_destinations(tmp_path):
    # get_toc() reports page -1 for entries whose destination is not a page
    # (external/web bookmarks, broken links); they must not become segments.
    path = make_pdf(
        tmp_path,
        [PDF_FILLER, PDF_FILLER, PDF_FILLER, PDF_FILLER],
        toc=[
            [1, "Chapter One", 1],
            [1, "Chapter Two", 2],
            [1, "Broken Dest", -1],
            [1, "Chapter Three", 3],
        ],
    )
    full_text, meta = book.parse(str(path))
    titles = [s["title"] for s in meta["segments"]]
    assert titles == ["Chapter One", "Chapter Two", "Chapter Three"]
    offsets = [s["offset"] for s in meta["segments"]]
    assert offsets == sorted(offsets)
    assert len(set(offsets)) == len(offsets)
    assert "The quick brown fox" in full_text[offsets[0]:offsets[1]]


def test_parse_pdf_book_outline_all_unresolved_falls_back(tmp_path):
    path = make_pdf(
        tmp_path,
        ["Introduction\n" + PDF_FILLER, "Conclusion\n" + PDF_FILLER],
        toc=[[1, "Publisher Website", -1]],
    )
    _, meta = book.parse(str(path))
    titles = [s["title"] for s in meta["segments"]]
    assert titles == ["Introduction", "Conclusion"]


def test_parse_pdf_book_without_outline_falls_back_to_sections(tmp_path):
    path = make_pdf(
        tmp_path,
        ["Introduction\n" + PDF_FILLER, "Conclusion\n" + PDF_FILLER],
    )
    _, meta = book.parse(str(path))
    assert meta["source_type"] == "book"
    titles = [s["title"] for s in meta["segments"]]
    assert titles == ["Introduction", "Conclusion"]
    assert [s["pages"] for s in meta["segments"]] == [1, 2]


def test_parse_pdf_book_without_outline_or_headings_single_segment(tmp_path):
    path = make_pdf(tmp_path, [PDF_FILLER, PDF_FILLER])
    _, meta = book.parse(str(path))
    assert meta["segments"] == [
        {"title": "Full text", "start_s": None, "pages": 1, "offset": 0}
    ]


def test_chapter_text_keeps_code_indentation_and_superscripts():
    text, _, _ = book._chapter_text(
        "<html><body><p>Run <code>git status -s</code>:</p>"
        "<pre> M README\nMM Rakefile\n    nested: true</pre>"
        "<p>   About 2<sup>80</sup> hashes​.</p></body></html>"
    )
    assert text.splitlines() == [
        "Run git status -s:",
        "",
        " M README",
        "MM Rakefile",
        "    nested: true",
        "About 2^80 hashes.",
    ]


@pytest.mark.parametrize(
    "title,flagged",
    [("Table of Contents", True), ("Contributors", True), ("Dedications", True),
     ("Copyright Page", True), ("Getting Started", False), ("Index Funds", False)],
)
def test_front_matter_titles(title, flagged):
    assert bool(book.FRONT_MATTER_RE.match(title)) is flagged


def test_content_chapters_are_not_front_matter(tmp_path):
    _, meta = book.parse(str(make_epub(tmp_path)))
    assert not any(s.get("front_matter") for s in meta["segments"])
