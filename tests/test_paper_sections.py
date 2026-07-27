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


def test_detect_sections_finds_known_headings():
    titles = [s["title"] for s in paper.detect_sections(SAMPLE)]
    assert titles == ["Abstract", "Introduction", "Results", "Limitations", "References"]


def test_detect_sections_offsets_point_at_headings():
    sections = paper.detect_sections(SAMPLE)
    for section in sections:
        line = SAMPLE[section["offset"]:].splitlines()[0]
        assert section["title"].lower() in line.lower()


def test_detect_sections_falls_back_to_full_text():
    assert paper.detect_sections("no headings here at all") == [
        {"title": "Full text", "offset": 0}
    ]
