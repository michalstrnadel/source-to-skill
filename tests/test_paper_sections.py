from extractor.parsers import paper

SAMPLE = """Attention Is All You Need

Abstract
We propose a new architecture.

1. Introduction
Sequence models dominate.

3.1 Scaled Dot-Product Attention
Details here.

4. Results
It works.

Limitations
Compute hungry.

References
[1] Prior work.
"""

# Abridged PyMuPDF get_text() output of arXiv 1706.03762: section numbers
# sit on their own line, page numbers trail each page, tables spill
# numbers line by line, and the appendix follows the references.
ATTENTION = """Attention Is All You Need
Ashish Vaswani
Abstract
Our model achieves 28.4 BLEU on the WMT 2014 English-
to-German translation task.
31st Conference on Neural Information Processing Systems (NIPS 2017), Long Beach, CA, USA.
arXiv:1706.03762v7  [cs.CL]  2 Aug 2023

1
Introduction
Recurrent neural networks, long short-term memory [13] and gated recurrent [7] neural networks
2
Background
The goal of reducing sequential computation also forms the foundation.
3
Model Architecture
Most competitive neural sequence transduction models have an encoder-decoder structure [5, 2, 35].
2

3.1
Encoder and Decoder Stacks
Encoder: The encoder is composed of a stack of N = 6 identical layers.
3.2
Attention
An attention function can be described as mapping a query.
3
Layer
Type
1
√dk . Additive attention computes the compatibility function.
4
Why Self-Attention
In this section we compare various aspects of self-attention layers.
6
5
Training
This section describes the training regime for our models.
5.1
Training Data and Batching
We trained on the standard WMT 2014 English-German dataset.
12
768
24 1024 16 64
6
Results
6.1
Machine Translation
On the WMT 2014 English-to-German translation task, the big transformer model.
7
Conclusion
In this work, we presented the Transformer.
Acknowledgements
We are grateful to Nal Kalchbrenner and Stephan Gouws.
References
[1] Jimmy Lei Ba, Jamie Ryan Kiros, and Geoffrey E Hinton. Layer normalization. arXiv preprint
arXiv:1607.06450, 2016.
[2] Dzmitry Bahdanau, Kyunghyun Cho, and Yoshua Bengio. Neural machine translation by jointly
learning to align and translate. CoRR, abs/1409.0473, 2014.
10

[3] Jonas Gehring, Michael Auli, David Grangier, Denis Yarats, and Yann N. Dauphin. Convolu-
tional sequence to sequence learning. arXiv preprint arXiv:1705.03122v2, 2017.
[4] Alex Graves.
Generating sequences with recurrent neural networks.
arXiv preprint
arXiv:1308.0850, 2013.
12

A Attention Visualizations
It
is
in
this
spirit
<EOS>
Figure 3: An example of the attention mechanism following long-distance dependencies.
13
"""


def titles(text, **kwargs):
    return [s["title"] for s in paper.detect_sections(text, **kwargs)]


def test_detect_sections_finds_known_headings():
    assert titles(SAMPLE) == [
        "Abstract", "Introduction", "Results", "Limitations", "References",
    ]


def test_detect_sections_offsets_point_at_headings():
    sections = paper.detect_sections(SAMPLE)
    for section in sections:
        line = SAMPLE[section["offset"]:].splitlines()[0]
        assert section["title"].lower() in line.lower()


def test_detect_sections_falls_back_to_full_text():
    assert paper.detect_sections("no headings here at all") == [
        {"title": "Full text", "offset": 0}
    ]


def test_detect_sections_numbered_headings_on_their_own_line():
    assert titles(ATTENTION) == [
        "Abstract", "Introduction", "Background", "Model Architecture",
        "Why Self-Attention", "Training", "Results", "Conclusion",
        "Acknowledgements", "References",
        "Appendix A: Attention Visualizations",
    ]


def test_detect_sections_offsets_start_at_number_line():
    by_title = {s["title"]: s for s in paper.detect_sections(ATTENTION)}
    assert ATTENTION[by_title["Model Architecture"]["offset"]:].startswith(
        "3\nModel Architecture\n"
    )
    assert ATTENTION[
        by_title["Appendix A: Attention Visualizations"]["offset"]:
    ].startswith("A Attention Visualizations\n")


def test_detect_sections_same_line_numbered_headings():
    text = (
        "Abstract\nShort abstract text.\n"
        "1 Introduction\nIntro body.\n"
        "2 Deep residual learning\nBody text.\n"
        "2.1 Residual Learning\nSubsection stays inside its parent.\n"
        "3. Experiments\nBody.\n"
        "References\n[1] A. Author. A paper. 2020.\n"
        "Appendix B: Extra Results\nMore.\n"
    )
    assert titles(text) == [
        "Abstract", "Introduction", "Deep residual learning", "Experiments",
        "References", "Appendix B: Extra Results",
    ]


def test_detect_sections_rejects_false_positives():
    text = (
        "1 Introduction\n"
        "2 models were trained on eight GPUs for three days.\n"  # lowercase prose
        "24 Layers\n"  # number > 20
        "3 The model is trained with a very long sentence that keeps going and "
        "going well past any reasonable heading length\n"
        "2\n"  # page number, then the page-break blank line
        "\n"
        "Layer\n"
        "3 √dk scaling\n"  # math, not a title
        "4 1024 16\n"  # table row
        "2 Method\n"
        "Body.\n"
    )
    assert titles(text) == ["Introduction", "Method"]


def test_detect_sections_skips_table_of_contents():
    text = (
        "Abstract\nText.\nContents\n"
        "1\nIntroduction\n3\n"
        "2\nApproach\n6\n"
        "2.1\nModel and Architectures . . . . . . . . . . 8\n"
        "A Details of Common Crawl Filtering\n43\n"
        "1\nIntroduction\nReal intro text.\n"
        "2\nApproach\nReal approach text.\n"
        "A\nDetails of Common Crawl Filtering\nAppendix body.\n"
        "References\n[ADG+16] M. Andrychowicz. Learning to learn. 2016.\n"
    )
    sections = paper.detect_sections(text)
    assert [s["title"] for s in sections] == [
        "Abstract", "Introduction", "Approach",
        "Appendix A: Details of Common Crawl Filtering", "References",
    ]
    intro = next(s for s in sections if s["title"] == "Introduction")
    assert text[intro["offset"]:].startswith("1\nIntroduction\nReal intro")


def test_detect_sections_ignores_numbered_lines_after_references():
    text = (
        "1 Introduction\nBody.\n"
        "References\n"
        "[1] A. Author. A paper title. In Proceedings, 2020.\n"
        "2 Method\n"
        "[2] B. Writer. Another. 2021.\n"
    )
    assert titles(text) == ["Introduction", "References"]


def test_detect_sections_font_headings_mark_unlettered_appendix():
    text = ATTENTION.replace("A Attention Visualizations", "Attention Visualizations")
    assert titles(text)[-1] == "References"
    assert titles(text, font_headings={"Attention Visualizations"})[-1] == (
        "Appendix: Attention Visualizations"
    )


def test_extract_references_splits_bracketed_entries():
    sections = paper.detect_sections(ATTENTION)
    refs = paper.extract_references(ATTENTION, sections)
    assert refs == [
        "[1] Jimmy Lei Ba, Jamie Ryan Kiros, and Geoffrey E Hinton. Layer "
        "normalization. arXiv preprint arXiv:1607.06450, 2016.",
        "[2] Dzmitry Bahdanau, Kyunghyun Cho, and Yoshua Bengio. Neural "
        "machine translation by jointly learning to align and translate. "
        "CoRR, abs/1409.0473, 2014.",
        "[3] Jonas Gehring, Michael Auli, David Grangier, Denis Yarats, and "
        "Yann N. Dauphin. Convolutional sequence to sequence learning. "
        "arXiv preprint arXiv:1705.03122v2, 2017.",
        "[4] Alex Graves. Generating sequences with recurrent neural "
        "networks. arXiv preprint arXiv:1308.0850, 2013.",
    ]


def test_extract_references_numbered_entries_without_brackets():
    text = (
        "1 Introduction\nBody.\n"
        "References\n"
        "1. Smith, J. A study of things.\nJournal of Stuff, 2019.\n"
        "2. Doe, A. Another study. 2020.\n"
        "7\n"
        "3. Roe, B. Third one, pages 1-\n10, 2021.\n"
    )
    refs = paper.extract_references(text, paper.detect_sections(text))
    assert refs == [
        "1. Smith, J. A study of things. Journal of Stuff, 2019.",
        "2. Doe, A. Another study. 2020.",
        "3. Roe, B. Third one, pages 1-10, 2021.",
    ]


def test_extract_references_alpha_keys():
    text = (
        "References\n"
        "[ADG+16] Marcin Andrychowicz, Misha Denil. Learning to learn\n"
        "by gradient descent. 2016.\n"
        "[AI19] WeChat AI. Tr-mt (ensemble), December 2019.\n"
    )
    refs = paper.extract_references(text, paper.detect_sections(text))
    assert len(refs) == 2
    assert refs[0].endswith("Learning to learn by gradient descent. 2016.")


def test_detect_sections_ignores_prose_line_ending_in_appendix_reference():
    text = (
        "1 Introduction\nThe exact procedure is detailed in\n"
        "Appendix C.\n"
        "We then evaluate the model.\n"
        "A\nDetails of Filtering\nBody.\n"
        "B\nDetails of Model Training\nBody.\n"
    )
    assert titles(text) == [
        "Introduction", "Appendix A: Details of Filtering",
        "Appendix B: Details of Model Training",
    ]
