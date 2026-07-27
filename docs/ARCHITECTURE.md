# Architecture

source-to-skill is split into two halves that never blur:

1. **Extractor** — deterministic Python (`scripts/extract.py` + the
   `extractor` package). Detects the source type, parses it with the right
   tool (`yt-dlp` for YouTube, PyMuPDF for papers), and normalizes the result
   into two files with a shared contract.
2. **Generator** — the user's own agent following the repo-root `SKILL.md`.
   It reads the normalized output and distills it into an installable skill.
   No API keys, no cloud calls: the LLM work happens inside whatever agent
   the user already runs (Claude Code, GitHub Copilot CLI, Amp).

```
 <youtube-url> | <arxiv-url> | paper.pdf
        │
        ▼
┌────────────────────── EXTRACTOR (Python, deterministic) ──────────────────┐
│  scripts/extract.py        entrypoint: dispatch, error reporting,        │
│        │                   JSON summary on stdout                        │
│        ▼                                                                 │
│  scripts/extractor/                                                      │
│    ├─ config.py            URL patterns · work dir · segment window ·    │
│    │                       token factor · optional-dependency map        │
│    ├─ utils.py             detect_source · slugify · token estimate ·    │
│    │                       output writing · ExtractError                 │
│    ├─ dependencies.py      probe optional deps · require() with install  │
│    │                       hint · `--check` report                       │
│    └─ parsers/                                                           │
│         ├─ youtube.py      yt-dlp metadata · caption track pick (manual  │
│         │                  preferred, auto fallback) · VTT parsing ·     │
│         │                  chapter segmentation (10-min windows fallback)│
│         └─ paper.py        PyMuPDF text · section heuristics · DOI/year  │
│                            detection · reference list · arXiv download  │
│                                                                          │
│  output → <tempdir>/source_skill_work/                                   │
│    full_text.txt    normalized text, segment-addressable by offset       │
│    metadata.json    shared contract (see below)                          │
└──────────────────────────────────────────────────────────────────────────┘
        │
        ▼
┌────────────────────── GENERATOR (agent, follows SKILL.md) ────────────────┐
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
        └─ paper skill:
             SKILL.md           TL;DR + key claims with evidence
             methods.md · findings.md · limitations.md
             glossary.md · citations.md
```

## The shared metadata contract

Both parsers emit the same two files. The generator branches only on
`metadata.json` fields — never on parser internals — which is what makes new
source types cheap to add.

```json
{
  "source_type": "youtube | paper",
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

- `start_s` — start timestamp in seconds (video only; `null` for papers).
  This is what lets the generator emit `<origin>&t=<start_s>s` deep links.
- `pages` — 1-based page where the section starts (papers only; `null` for
  video).
- `offset` — character offset into `full_text.txt`. Each segment's text runs
  from its own offset to the next segment's offset, so the generator can read
  a large source one slice at a time.

Each parser also adds type-specific fields the templates use: video adds
`channel`, `upload_date`, `duration_s`, `captions` (`manual` or `auto`);
paper adds `authors`, `year`, `doi`, `page_count`, and a raw `references`
list.

## Design principles

1. **Structure, not summaries.** Generated skills carry frameworks, decision
   rules, anti-patterns, and concrete numbers — never padded prose or long
   verbatim passages.
2. **On-demand loading.** The generated `SKILL.md` stays around ~4k tokens;
   segments, findings, and glossaries cost tokens only when a question
   actually needs them.
3. **Graceful degradation.** A video without chapters segments into fixed
   10-minute windows; a paper with unrecognized headings falls back to a
   single "Full text" section; a missing optional dependency fails with the
   exact `pip install` hint. Hard errors are reserved for cases where output
   would be garbage: no captions at all, or a PDF with no text layer.
4. **Verify artefacts, not exit codes.** A zero exit status proves nothing.
   The generator checks that every promised file exists and is non-empty,
   and `tools/validate_skill.py` must print `OK: skill is valid` before the
   run counts as done.

## Key components

| Path | Responsibility |
|------|----------------|
| `scripts/extract.py` | entrypoint: dispatch, error reporting, JSON summary |
| `scripts/extractor/config.py` | URL patterns, work dir, optional-dependency map |
| `scripts/extractor/utils.py` | source detection, slugify, token estimate, output writing |
| `scripts/extractor/dependencies.py` | dependency probing, `--check` report |
| `scripts/extractor/parsers/youtube.py` | captions + chapter segmentation via yt-dlp |
| `scripts/extractor/parsers/paper.py` | PDF text + section/reference detection via PyMuPDF |
| `tools/validate_skill.py` | lints a generated skill (frontmatter, links, empty files) |
| `SKILL.md` | the generator spec (Steps 1–6) — this *is* the skill |

## Extending

**Adding a source type** is a four-file change plus a template:

1. `scripts/extractor/parsers/<type>.py` — implement
   `parse(source) -> (full_text, metadata)` returning the shared contract.
   Fill `start_s`/`pages` with `null` where they do not apply, but always
   emit `offset`.
2. `scripts/extractor/config.py` — add the URL patterns or file extensions
   that identify the source, and register any optional dependency in
   `OPTIONAL_DEPS` (module name → pip package + what it is needed for) so
   `--check` and the install-hint errors cover it automatically.
3. `scripts/extractor/utils.py` — add a branch to `detect_source` returning
   the new type name, and wire the dispatch in `scripts/extract.py`.
4. `SKILL.md` — add a generation template for the new `source_type` under
   Step 5, following the existing video/paper shape.

Back it with offline tests (fixtures, no network — see `tests/`), and the
generator side needs no other changes: it already reads only the contract.

**Changing generation behavior** means editing the relevant step in
`SKILL.md`. Keep it lean — it is loaded on every run of the skill.
