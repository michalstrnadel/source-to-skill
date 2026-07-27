import pytest

fitz = pytest.importorskip("fitz")

from extractor.parsers import paper
from extractor.utils import ExtractError

PAGE1 = """Deep Nets for Cats

Abstract
Cats are classified with 99 percent accuracy using deep networks trained on
one million images collected in 2024 from public archives and volunteers.
This paper reports the full training protocol and its cost profile in detail.
doi 10.1234/cats.2024.001
"""

PAGE2 = """Methods
We train a convolutional network for ninety epochs using stochastic gradient
descent with momentum and a cosine learning rate schedule over eight GPUs.

Results
Accuracy reaches 99 percent on the held-out set of one hundred thousand cats.

Limitations
Only cats are supported and the dataset skews toward indoor photography.

References
[1] A. Author. Cats and nets. 2023.
[2] B. Writer. More cats. 2022.
"""


def make_pdf(tmp_path, pages, name="paper.pdf"):
    path = tmp_path / name
    doc = fitz.open()
    for text in pages:
        page = doc.new_page()
        page.insert_text((72, 72), text)
    doc.save(path)
    doc.close()
    return path


def test_parse_extracts_sections_pages_and_metadata(tmp_path):
    path = make_pdf(tmp_path, [PAGE1, PAGE2])
    full_text, meta = paper.parse(str(path))
    assert meta["source_type"] == "paper"
    assert meta["doi"] == "10.1234/cats.2024.001"
    assert meta["page_count"] == 2
    titles = [s["title"] for s in meta["segments"]]
    assert titles == ["Abstract", "Methods", "Results", "Limitations", "References"]
    by_title = {s["title"]: s for s in meta["segments"]}
    assert by_title["Abstract"]["pages"] == 1
    assert by_title["Methods"]["pages"] == 2
    assert all(s["start_s"] is None for s in meta["segments"])
    assert full_text[by_title["Results"]["offset"]:].lower().startswith("results")
    assert len(meta["references"]) == 2


def test_parse_rejects_pdf_without_text_layer(tmp_path):
    path = make_pdf(tmp_path, ["", ""], name="scanned.pdf")
    with pytest.raises(ExtractError, match="no usable text layer"):
        paper.parse(str(path))


def test_parse_rejects_missing_file():
    with pytest.raises(ExtractError, match="PDF not found"):
        paper.parse("/nonexistent/nope.pdf")


def test_doi_strips_trailing_punctuation(tmp_path):
    page1 = PAGE1.replace(
        "doi 10.1234/cats.2024.001", "as shown (doi:10.1234/abc.def), later"
    )
    path = make_pdf(tmp_path, [page1, PAGE2])
    _, meta = paper.parse(str(path))
    assert meta["doi"] == "10.1234/abc.def"


def test_year_skips_implausible_numbers(tmp_path):
    page1 = PAGE1.replace(
        "one million images collected in 2024",
        "a context window of 2048 tokens on images collected in 2024",
    ).replace("doi 10.1234/cats.2024.001", "doi 10.1234/cats.001")
    path = make_pdf(tmp_path, [page1, PAGE2])
    _, meta = paper.parse(str(path))
    assert meta["year"] == 2024


def test_resolve_rejects_non_arxiv_urls():
    with pytest.raises(ExtractError, match="arXiv"):
        paper._resolve("https://openreview.net/pdf/x.pdf")


def test_resolve_downloads_arxiv_pdf(tmp_path, monkeypatch):
    downloaded = {}

    def fake_urlretrieve(url, target):
        downloaded["url"] = url
        make_pdf(tmp_path, [PAGE1, PAGE2], name="dl.pdf").rename(target)

    monkeypatch.setattr(paper.config, "work_dir", lambda: tmp_path / "work")
    monkeypatch.setattr(paper.urllib.request, "urlretrieve", fake_urlretrieve)
    path = paper._resolve("https://arxiv.org/abs/1706.03762")
    assert downloaded["url"] == "https://arxiv.org/pdf/1706.03762"
    assert path.name == "arxiv-1706.03762.pdf"
    assert path.exists()
