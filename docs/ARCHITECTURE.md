# Architecture

source-to-skill is split into two halves that never blur:

1. **Extractor** — deterministic Python (`scripts/extract.py` + the
   `extractor` package). Detects the source type (with an optional `--type`
   override), parses it with the right tool (`yt-dlp` for YouTube videos
   and playlists, PyMuPDF for papers and PDF books, the standard library
   for EPUBs, web articles, and GitHub repos), and normalizes the result
   into two files with a shared contract.
2. **Generator** — the user's own agent following the skill's `SKILL.md`.
   It reads the normalized output and distills it into an installable skill.
   No API keys, no cloud calls: the LLM work happens inside whatever agent
   the user already runs (Claude Code, GitHub Copilot CLI, Amp).

Everything ships in the self-contained skill folder
`skills/source-to-skill/` (SKILL.md + `scripts/` + `tools/`), which is
what gets installed — as a Claude Code plugin via the repo's
`.claude-plugin/` marketplace, or by copying/symlinking the folder into an
agent's skills directory. All paths below are relative to that folder.

```
 <youtube-url> | <playlist-url> | <arxiv-url> | <article-url> |
 <github-repo-url> | paper.pdf | book.epub | book.pdf --type book
        │
        ▼
┌────────────────────── EXTRACTOR (Python, deterministic) ─────────────────┐
│  scripts/extract.py        entrypoint: --type override, dispatch,        │
│        │                   error reporting, JSON summary on stdout       │
│        ▼                                                                 │
│  scripts/extractor/                                                      │
│    ├─ config.py            source types · URL patterns · work dir ·      │
│    │                       segment window · token factor ·               │
│    │                       optional-dependency map                       │
│    ├─ utils.py             detect_source (--type validation) · slugify · │
│    │                       token estimate · output writing · ExtractError│
│    ├─ dependencies.py      probe optional deps · require() with install  │
│    │                       hint · `--check` report                       │
│    └─ parsers/                                                           │
│         ├─ youtube.py      yt-dlp metadata · caption track pick (manual  │
│         │                  preferred, auto fallback) · VTT parsing ·     │
│         │                  chapter segmentation (10-min windows fallback)│
│         ├─ playlist.py     yt-dlp flat listing · per-video captions via  │
│         │                  the youtube parser · captionless videos       │
│         │                  skipped with a warning (never fatal)          │
│         ├─ paper.py        PyMuPDF text · section heuristics · DOI/year  │
│         │                  detection · reference list · arXiv download   │
│         ├─ book.py         EPUB via stdlib (zip · OPF spine · toc.ncx /  │
│         │                  nav.xhtml titles) · PDF books via outline     │
│         │                  chapters (section-detection fallback)         │
│         ├─ article.py      stdlib fetch + HTMLParser extraction ·        │
│         │                  article > main > body scoping · h1-h3         │
│         │                  segment boundaries · og:title/author/date     │
│         └─ repo.py         codeload tarball (no git clone) · README +    │
│                            top-level *.md + docs/**/*.md · safe tar      │
│                            extraction · ~2 MB text cap                   │
│                                                                          │
│  output → <tempdir>/source_skill_work/                                   │
│    full_text.txt    normalized text, segment-addressable by offset       │
│    metadata.json    shared contract (see below)                          │
└──────────────────────────────────────────────────────────────────────────┘
        │
        ▼
┌────────────────────── GENERATOR (agent, follows SKILL.md) ───────────────┐
│  Step 1  run extract.py; on failure report and stop                      │
│  Step 2  show title + est_tokens, confirm cost with the user             │
│  Step 3  analyze structure; large sources read segment-by-segment        │
│          via `offset`, never in one go                                   │
│  Step 4  ask install target (user-level or project-local skills dir)     │
│  Step 5  generate from the `source_type` template                        │
│  Step 6  verify artefacts + run tools/validate_skill.py                  │
└──────────────────────────────────────────────────────────────────────────┘
        │
        ▼
 <skills-home>/<slug>/          e.g. ~/.claude/skills/, ~/.agents/skills/,
        │                            ~/.copilot/skills/, ./.claude/skills/
        ├─ video skill:
        │    SKILL.md           core ideas + timestamped segment index
        │    segments/NN-*.md   one per segment, opens with a &t= deep link
        │    cheatsheet.md      actionable steps and decision rules
        ├─ playlist (course) skill:
        │    SKILL.md           course overview + lesson index
        │    lessons/NN-*.md    one per video, opens with the video URL
        │    cheatsheet.md      steps and rules across the course
        ├─ paper skill:
        │    SKILL.md           TL;DR + key claims with evidence
        │    methods.md · findings.md · limitations.md
        │    glossary.md · citations.md
        ├─ book skill:
        │    SKILL.md           core mental models + chapter index
        │    chapters/NN-*.md   one per chapter, loaded on demand
        │    glossary.md        key terms with chapter references
        │    cheatsheet.md      decision rules, techniques, anti-patterns
        ├─ article skill:
        │    SKILL.md           thesis + key claims, link to the original
        │    highlights.md      the passages worth keeping (short quotes)
        └─ repo skill:
             SKILL.md           what it does + install + usage + doc index
             guides/*.md        distilled per doc area
             cheatsheet.md      commands and snippets
```

## The shared metadata contract

All parsers emit the same two files. The generator branches only on
`metadata.json` fields — never on parser internals — which is what makes new
source types cheap to add.

```json
{
  "source_type": "youtube | playlist | paper | book | article | repo",
  "title": "...",
  "origin": "url or file path",
  "language": "en",
  "words": 12345,
  "est_tokens": 16460,
  "segments": [
    {"title": "...", "start_s": 842, "pages": null, "offset": 10234}
  ]
}
```

Per segment:

- `start_s` — start timestamp in seconds (video only; `null` for papers and
  books). This is what lets the generator emit `<origin>&t=<start_s>s` deep
  links.
- `pages` — 1-based page where the section or chapter starts (PDF sources
  only; `null` for video and EPUB books).
- `offset` — character offset into `full_text.txt`. Each segment's text runs
  from its own offset to the next segment's offset, so the generator can read
  a large source one slice at a time.
- `url` — playlist segments only: the video's URL, which generated lesson
  files open with. Other source types omit the key.

Each parser also adds type-specific fields the templates use: video adds
`channel`, `upload_date`, `duration_s`, `captions` (`manual` or `auto`);
playlist adds `channel`, `video_count`, and `skipped` (videos dropped for
missing captions, each with title, url, and reason); paper adds `authors`,
`year`, `doi`, `page_count`, and a raw `references` list; book adds
`author` (and `page_count` for PDF books); article adds `author`, `date`,
and `language` when the page declares them; repo adds `owner`, `repo`, and
`file_count`.

## Design principles

1. **Structure, not summaries.** Generated skills carry frameworks, decision
   rules, anti-patterns, and concrete numbers — never padded prose or long
   verbatim passages.
2. **On-demand loading.** The generated `SKILL.md` stays around ~4k tokens;
   segments, findings, and glossaries cost tokens only when a question
   actually needs them.
3. **Graceful degradation.** A video without chapters segments into fixed
   10-minute windows; a playlist video without captions is skipped with a
   warning and recorded in `skipped`, never failing the playlist; a paper
   with unrecognized headings falls back to a single "Full text" section;
   a PDF book without an outline falls back to the same section detection;
   an EPUB chapter missing from the table of contents (or a whole
   malformed `toc.ncx`) is titled from its first `<h1>`, its `<title>`, or
   "Chapter N"; a repo over the ~2 MB text cap drops later doc files with
   a warning; a missing optional dependency fails with the exact
   `pip install` hint. Hard errors are reserved for cases where output
   would be garbage: no captions at all (in a video, or across a whole
   playlist), a PDF with no text layer, a page with no readable article
   text, or a repo with no README and no docs.
4. **Verify artefacts, not exit codes.** A zero exit status proves nothing.
   The generator checks that every promised file exists and is non-empty,
   and `tools/validate_skill.py` must print `OK: skill is valid` before the
   run counts as done.

## Key components

| Path | Responsibility |
|------|----------------|
| `scripts/extract.py` | entrypoint: dispatch (honors `--type`), error reporting, JSON summary |
| `scripts/extractor/config.py` | source types, URL patterns, work dir, optional-dependency map |
| `scripts/extractor/utils.py` | source detection (validates forced `--type`), slugify, token estimate, output writing |
| `scripts/extractor/dependencies.py` | dependency probing, `--check` report |
| `scripts/extractor/parsers/youtube.py` | captions + chapter segmentation via yt-dlp |
| `scripts/extractor/parsers/playlist.py` | flat playlist listing + per-video captions; captionless videos skipped |
| `scripts/extractor/parsers/paper.py` | PDF text + section/reference detection via PyMuPDF |
| `scripts/extractor/parsers/book.py` | EPUB chapters via stdlib zip/XML; PDF book chapters via outline |
| `scripts/extractor/parsers/article.py` | web page fetch + readable-article extraction via stdlib HTMLParser |
| `scripts/extractor/parsers/repo.py` | GitHub tarball download + README/docs selection, traversal-safe extract |
| `tools/validate_skill.py` | lints a generated skill (frontmatter, links, empty files) |
| `SKILL.md` | the generator spec (Steps 1–6) — this *is* the skill |

## Extending

**Adding a source type** is a four-file change plus a template:

1. `scripts/extractor/parsers/<type>.py` — implement
   `parse(source) -> (full_text, metadata)` returning the shared contract.
   Fill `start_s`/`pages` with `null` where they do not apply, but always
   emit `offset`.
2. `scripts/extractor/config.py` — add the new name to `SOURCE_TYPES`, add
   any URL patterns that identify the source, and register any optional
   dependency in `OPTIONAL_DEPS` (module name → pip package + what it is
   needed for) so `--check` and the install-hint errors cover it
   automatically. File extensions are not registered here — they are
   matched in `utils._possible_types` (step 3).
3. `scripts/extractor/utils.py` — teach `_possible_types` which URL
   patterns or file extensions map to the new type (this is what
   `detect_source` and the `--type` validation read), and add the parser
   to the `PARSERS` table in `scripts/extract.py`.
4. `SKILL.md` — add a generation template for the new `source_type` under
   Step 5, following the existing video/paper shape.

Back it with offline tests (fixtures, no network — see `tests/`), and the
generator side needs no other changes: it already reads only the contract.

**Changing generation behavior** means editing the relevant step in
`SKILL.md`. Keep it lean — it is loaded on every run of the skill.
