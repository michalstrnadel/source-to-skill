# Changelog

All notable changes to **source-to-skill** are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-07-27

Books join videos and papers: EPUBs with zero new dependencies, PDF books
via a type override.

### Added

- **Book parser** (`scripts/extractor/parsers/book.py`) — EPUB books parsed
  with the Python standard library alone (zip → `META-INF/container.xml` →
  OPF spine; chapter titles from `toc.ncx` or the EPUB3 `nav.xhtml`, falling
  back to the first `<h1>`, the document `<title>`, then "Chapter N"; tags
  stripped and entities decoded via `html.parser`). PDF books reuse PyMuPDF:
  chapters come from the top-level PDF outline, falling back to section
  detection. Metadata uses `source_type: "book"` and adds `author` (EPUB
  `dc:creator` / PDF metadata). Malformed EPUBs (bad zip, missing
  container.xml, unreadable OPF, empty spine) fail with clear errors; a
  malformed `toc.ncx` falls back to nav/heading titles instead of aborting,
  spine items missing from the archive are skipped with a stderr warning,
  and unresolved PDF outline destinations are ignored.
- **`--type` override** — `extract.py <source> [--type youtube|paper|book]`
  forces the parser when auto-detection is not enough (a PDF book vs. a PDF
  paper); `.epub` auto-detects as book, unknown types and impossible
  source/type combinations are rejected with clear errors.
- **Book skill template** (repo-root `SKILL.md`, Step 5) — core mental
  models plus a chapter index table in the generated SKILL.md, on-demand
  `chapters/NN-<slug>.md` files, `glossary.md` with chapter references, and
  `cheatsheet.md` with decision rules and anti-patterns.

## [0.1.0] - 2026-07-27

First public release: YouTube videos and academic papers in, installable
agent skills out.

### Added

- **YouTube parser** (`scripts/extractor/parsers/youtube.py`) — captions via
  yt-dlp (manual subtitles preferred, auto-generated as fallback; English
  variants preferred), VTT parsing with auto-caption de-duplication, and
  segmentation by the video's own chapters with fixed 10-minute windows as
  fallback. Every segment records its start timestamp so generated skills
  can deep-link back into the video with `&t=`.
- **Paper parser** (`scripts/extractor/parsers/paper.py`) — text extraction
  via PyMuPDF from local PDFs or modern arXiv URLs (downloaded
  automatically), heuristic section detection (Abstract through References,
  with a safe full-text fallback), DOI/year detection, per-section page
  numbers, and a raw reference list. Scanned PDFs without a text layer fail
  with a clear "OCR not supported yet" error.
- **Extractor CLI** (`scripts/extract.py`) — detects the source type,
  dispatches to the right parser, and writes `full_text.txt` +
  `metadata.json` (the shared segment contract: `title`, `start_s`, `pages`,
  `offset`) to the work dir. `--check` reports each optional dependency
  (yt-dlp, PyMuPDF) with an exact install hint; extraction errors state what
  failed and the next step.
- **Generator spec** (repo-root `SKILL.md`) — the six-step agent workflow:
  extract, confirm token cost, analyze structure (segment-by-segment reads
  for large sources), choose an install target, generate, verify. Video
  skills get a timestamped segment index, per-segment files opening with a
  deep link, and a cheatsheet; paper skills get a TL;DR plus
  `methods.md`, `findings.md`, `limitations.md`, `glossary.md`, and
  `citations.md`.
- **Skill validator** (`tools/validate_skill.py`) — checks generated skills
  for valid frontmatter (name matches the directory, description within
  limits), resolvable markdown links, and no empty files; prints
  `OK: skill is valid` on success.
- **Offline test suite** — pytest coverage for source detection, VTT
  parsing, segmentation, paper section detection, dependency probing, the
  CLI, and the validator; yt-dlp is mocked and the PDF fixture is generated
  locally, so no test touches the network.
- MIT license; Python ≥ 3.10.
