"""arXiv metadata, title, and year resolution for papers (offline)."""
import io
from pathlib import Path

import pytest

fitz = pytest.importorskip("fitz")

from extractor.parsers import paper

FIXTURES = Path(__file__).parent / "fixtures"
ATOM = (FIXTURES / "arxiv_1706.03762.xml").read_bytes()

BODY = (
    "Abstract\n"
    "Our model achieves 28.4 BLEU on the WMT 2014 English-to-German\n"
    "translation task, improving over the existing best results by 2 BLEU.\n"
    "We show that the Transformer generalizes well to other tasks by\n"
    "applying it successfully to English constituency parsing with large\n"
    "and limited training data and many other words to pass the minimum.\n"
)


def make_pdf(tmp_path, pages, name="paper.pdf", metadata=None):
    """pages: list of [(text, fontsize, fontname)] spans or plain strings."""
    path = tmp_path / name
    doc = fitz.open()
    for page_spec in pages:
        page = doc.new_page()
        if isinstance(page_spec, str):
            page_spec = [(page_spec, 11, "helv")]
        y = 72
        for text, size, font in page_spec:
            page.insert_text((72, y), text, fontsize=size, fontname=font)
            y += (text.count("\n") + 1) * size * 1.3 + 6
    if metadata:
        doc.set_metadata(metadata)
    doc.save(path)
    doc.close()
    return path


def fake_urlopen_factory(pdf_bytes, atom=ATOM, calls=None):
    def fake_urlopen(url, timeout=None):
        if calls is not None:
            calls.append((url, timeout))
        if "export.arxiv.org/api/query" in url:
            if isinstance(atom, Exception):
                raise atom
            return io.BytesIO(atom)
        return io.BytesIO(pdf_bytes)

    return fake_urlopen


# --- arXiv API -----------------------------------------------------------


def test_fetch_arxiv_metadata_parses_atom(monkeypatch):
    calls = []
    monkeypatch.setattr(
        paper.urllib.request, "urlopen", fake_urlopen_factory(b"", calls=calls)
    )
    meta = paper.fetch_arxiv_metadata("1706.03762")
    assert calls == [
        (
            "https://export.arxiv.org/api/query?id_list=1706.03762",
            paper.config.FETCH_TIMEOUT_S,
        )
    ]
    assert meta["title"] == "Attention Is All You Need"
    assert meta["authors"][0] == "Ashish Vaswani"
    assert meta["authors"][-1] == "Illia Polosukhin"
    assert len(meta["authors"]) == 8
    assert meta["year"] == 2017
    assert meta["doi"] is None


def test_fetch_arxiv_metadata_normalizes_title_and_reads_doi(monkeypatch):
    atom = ATOM.replace(
        b"<title>Attention Is All You Need</title>",
        b"<title>Attention Is\n      All   You Need</title>"
        b"<arxiv:doi>10.1000/xyz.123</arxiv:doi>",
    )
    monkeypatch.setattr(
        paper.urllib.request, "urlopen", fake_urlopen_factory(b"", atom=atom)
    )
    meta = paper.fetch_arxiv_metadata("1706.03762")
    assert meta["title"] == "Attention Is All You Need"
    assert meta["doi"] == "10.1000/xyz.123"


@pytest.mark.parametrize(
    "atom",
    [
        OSError("network down"),
        b"<not xml",
        b'<feed xmlns="http://www.w3.org/2005/Atom"></feed>',
        b'<feed xmlns="http://www.w3.org/2005/Atom"><entry>'
        b"<id>http://arxiv.org/api/errors#incorrect_id_format</id>"
        b"<title>Error</title></entry></feed>",
    ],
)
def test_fetch_arxiv_metadata_failure_returns_none_and_warns(
    monkeypatch, capsys, atom
):
    monkeypatch.setattr(
        paper.urllib.request, "urlopen", fake_urlopen_factory(b"", atom=atom)
    )
    assert paper.fetch_arxiv_metadata("1706.03762") is None
    assert "arXiv metadata" in capsys.readouterr().err


def test_parse_arxiv_url_uses_api_metadata(tmp_path, monkeypatch):
    pdf = make_pdf(tmp_path, [BODY, BODY], name="src.pdf").read_bytes()
    monkeypatch.setattr(paper.config, "work_dir", lambda: tmp_path / "work")
    monkeypatch.setattr(
        paper.urllib.request, "urlopen", fake_urlopen_factory(pdf)
    )
    _, meta = paper.parse("https://arxiv.org/abs/1706.03762")
    assert meta["title"] == "Attention Is All You Need"
    assert len(meta["authors"]) == 8
    assert meta["year"] == 2017
    assert meta["arxiv_id"] == "1706.03762"
    assert meta["abstract_url"] == "https://arxiv.org/abs/1706.03762"


def test_parse_arxiv_url_survives_api_failure(tmp_path, monkeypatch, capsys):
    page1 = [
        ("Attention Is All You Need", 17, "hebo"),
        ("arXiv:1706.03762v7  [cs.CL]  2 Aug 2023", 20, "helv"),
        (BODY, 10, "helv"),
    ]
    pdf = make_pdf(
        tmp_path, [page1, BODY], name="src.pdf",
        metadata={"creationDate": "D:20240410211143Z"},
    ).read_bytes()
    monkeypatch.setattr(paper.config, "work_dir", lambda: tmp_path / "work")
    monkeypatch.setattr(
        paper.urllib.request,
        "urlopen",
        fake_urlopen_factory(pdf, atom=OSError("api down")),
    )
    _, meta = paper.parse("https://arxiv.org/abs/1706.03762")
    assert "arXiv metadata" in capsys.readouterr().err
    assert meta["title"] == "Attention Is All You Need"
    assert meta["year"] == 2017  # arXiv id 1706, not WMT 2014 / creation 2024
    assert meta["arxiv_id"] == "1706.03762"


# --- title ---------------------------------------------------------------


def test_title_from_largest_font_skips_arxiv_stamp(tmp_path):
    page1 = [
        ("Provided proper attribution is provided.", 12, "helv"),
        ("Deep Residual Learning", 17, "hebo"),
        ("for Image Recognition", 17, "hebo"),
        ("Kaiming He", 12, "helv"),
        ("arXiv:1512.03385v1  [cs.CV]  10 Dec 2015", 20, "helv"),
        (BODY, 10, "helv"),
    ]
    path = make_pdf(tmp_path, [page1, BODY], name="resnet.pdf")
    _, meta = paper.parse(str(path))
    assert meta["title"] == "Deep Residual Learning for Image Recognition"
    assert meta["arxiv_id"] == "1512.03385"
    assert meta["year"] == 2015


def test_title_keeps_plausible_pdf_metadata(tmp_path):
    page1 = [("Some Other Big Line", 20, "hebo"), (BODY, 10, "helv")]
    path = make_pdf(
        tmp_path, [page1, BODY], metadata={"title": "A Real Paper Title"}
    )
    _, meta = paper.parse(str(path))
    assert meta["title"] == "A Real Paper Title"


@pytest.mark.parametrize(
    "bad_title",
    ["Microsoft Word - draft_v3.docx", "untitled", "paper_final_v2.pdf",
     "arxiv-1706.03762", "   "],
)
def test_title_rejects_implausible_pdf_metadata(tmp_path, bad_title):
    page1 = [("Cats Are Liquid", 18, "hebo"), (BODY, 10, "helv")]
    path = make_pdf(tmp_path, [page1, BODY], metadata={"title": bad_title})
    _, meta = paper.parse(str(path))
    assert meta["title"] == "Cats Are Liquid"


def test_pdf_metadata_authors_become_list(tmp_path):
    path = make_pdf(
        tmp_path, [BODY, BODY],
        metadata={"title": "A Real Paper Title", "author": "Ada Lovelace; Alan Turing"},
    )
    _, meta = paper.parse(str(path))
    assert meta["authors"] == ["Ada Lovelace", "Alan Turing"]


# --- year ----------------------------------------------------------------


def test_year_from_arxiv_id():
    assert paper.year_from_arxiv_id("1706.03762") == 2017
    assert paper.year_from_arxiv_id("2406.01234v2") == 2024
    assert paper.year_from_arxiv_id("hep-th/9901001") == 1999
    assert paper.year_from_arxiv_id(None) is None


@pytest.mark.parametrize(
    "text, expected",
    [
        ("trained on WMT 2014 data.\n31st Conference on Neural Information "
         "Processing Systems (NIPS 2017), Long Beach.", 2017),
        ("Results on ImageNet 2012.\nPublished at NeurIPS 2023.", 2023),
        ("COCO 2015 numbers.\nProceedings of the 37th ICML 2020, Vienna.", 2020),
        ("WMT 2014 data.\nIn Conference on Empirical Methods 2019.", 2019),
    ],
)
def test_venue_year(text, expected):
    assert paper.venue_year(text) == expected


def test_year_prefers_creation_date_over_dataset_years(tmp_path):
    page1 = BODY  # mentions only "WMT 2014"
    path = make_pdf(
        tmp_path, [page1, BODY], metadata={"creationDate": "D:20170612120000Z"}
    )
    _, meta = paper.parse(str(path))
    assert meta["year"] == 2017


def test_year_fallback_skips_dataset_names(tmp_path):
    page1 = BODY + "Data was collected in 2019 by volunteers.\n"
    path = make_pdf(tmp_path, [page1, BODY])
    _, meta = paper.parse(str(path))
    assert meta["year"] == 2019
