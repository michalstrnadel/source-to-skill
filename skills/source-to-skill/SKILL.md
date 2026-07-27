---
name: source-to-skill
description: Turn a YouTube video or playlist, academic paper (PDF / arXiv URL), book (EPUB, or PDF book via --type book), web article, or GitHub repository into an installable agent skill. Use when the user runs /source-to-skill, or asks to convert a video, talk, lecture, playlist, course, paper, PDF, book, EPUB, article, blogpost, or GitHub repo into a skill / structured reference.
---

# source-to-skill

Turn a knowledge source into a structured agent skill the user can load on
demand. Supported sources: YouTube video and playlist URLs, arXiv URLs,
local PDF papers, books (EPUB files, or PDF books via `--type book`), web
article URLs, and GitHub repository URLs.

Usage: `/source-to-skill <url-or-file> [skill-slug]` — for a PDF that is a
book rather than a paper, extract with `--type book`; for a
`watch?v=...&list=...` URL that should become the whole playlist, extract
with `--type playlist`.

## Step 1 — Extract

Run from this skill's directory (the folder containing this SKILL.md —
`scripts/` and `tools/` live next to it):

    python3 scripts/extract.py "<source>"

- `.epub` files are detected as books automatically. A `.pdf` defaults to
  the paper parser — when the PDF is a book, add the override:
  `python3 scripts/extract.py "<source>" --type book`. If it is unclear
  whether a PDF is a paper or a book, ask the user before extracting.
- `youtube.com/playlist?list=...` URLs are detected as playlists. A
  `watch?v=...&list=...` URL stays a single video — add `--type playlist`
  to extract the whole playlist instead; if it is unclear which the user
  wants, ask before extracting.
- In a playlist, videos without captions are skipped with a stderr warning
  and listed in `metadata.json` under `skipped` — report skipped videos to
  the user; extraction fails only when no video has usable captions.
- Bare `github.com/<owner>/<repo>` URLs are detected as repos (deeper
  paths are not); any other `http(s)` URL is treated as a web article.
- On dependency errors, run `python3 scripts/extract.py --check` and show the
  user the install hints. Do not install anything without asking.
- On any other ERROR, report it verbatim and stop.
- On success the command prints JSON with `work_dir`, `title`, `est_tokens`,
  and `segments`. All extracted content is in `<work_dir>/full_text.txt` and
  `<work_dir>/metadata.json`.

## Step 2 — Confirm cost

Tell the user the title, source type, and `est_tokens`, and ask to proceed.
Generation reads the full text once; skills built from it cost a fraction of
that per future question.

## Step 3 — Analyze structure

Read `metadata.json`. For large sources (over ~40k est_tokens) do NOT read
`full_text.txt` in one go — read it segment by segment using the `offset`
values (each segment's text runs to the next segment's offset).

## Step 4 — Choose install target

Ask the user where to install (default first):

1. `~/.claude/skills/<slug>/` (Claude Code, user-level)
2. `~/.agents/skills/<slug>/` (cross-agent)
3. `~/.copilot/skills/<slug>/` (GitHub Copilot CLI)
4. `./.claude/skills/<slug>/` (this project only, Claude Code)
5. `./.agents/skills/<slug>/` (this project only, cross-agent)
6. `./.github/skills/<slug>/` (this project only, GitHub Copilot)

`<slug>` is the second argument if given, else slugified from the title.

## Step 5 — Generate

Always write in English, regardless of source language. Extract structure —
frameworks, decision rules, anti-patterns, concrete numbers — never padded
summaries. Front-load the most important content in SKILL.md and keep it
under ~4k tokens; support files carry the detail.

For `source_type: youtube`:

- `SKILL.md` — frontmatter (name = slug; description = what the video
  teaches and when to load this skill), core ideas, then a segment index
  table: segment title, one-line takeaway, link `segments/NN-<slug>.md`.
- `segments/NN-<slug>.md` — one per segment, first line is the deep link
  `<origin>&t=<start_s>s` (use `?t=` if the origin URL has no query string),
  then the distilled content of that segment.
- `cheatsheet.md` — actionable steps, decision rules, and named techniques
  from the whole video.

For `source_type: playlist` (a course):

- `SKILL.md` — frontmatter as above, course overview (what the course
  teaches and in what order), then a lesson index table: lesson, one-line
  takeaway, link `lessons/NN-<slug>.md`.
- `lessons/NN-<slug>.md` — one per video, numbered in playlist order; the
  first line is the video URL (the segment's `url` field), then the
  distilled content of that lesson.
- `cheatsheet.md` — actionable steps, decision rules, and named techniques
  across the whole course.

For `source_type: paper`:

- `SKILL.md` — frontmatter as above, TL;DR (3 sentences max), key claims
  each with its supporting evidence and section reference, file index.
- `methods.md` — how the work was done; enough detail to assess validity.
- `findings.md` — results with concrete numbers and conditions.
- `limitations.md` — stated limitations plus caveats evident from methods.
- `glossary.md` — terms alphabetically, each with a one-line definition.
- `citations.md` — how to cite this paper (title, authors, year, DOI when
  present in metadata.json) and the reference list from `references`.

For `source_type: book`:

- `SKILL.md` — frontmatter as above, the book's core mental models and
  frameworks front-loaded, then a chapter index table: chapter, one-line
  takeaway, link `chapters/NN-<slug>.md`.
- `chapters/NN-<slug>.md` — one per chapter (numbered in reading order),
  loaded on demand: the chapter's frameworks, arguments, and concrete
  examples — not a retelling.
- `glossary.md` — key terms alphabetically, each with a one-line definition
  and the chapter it comes from.
- `cheatsheet.md` — decision rules, named techniques, and anti-patterns
  from the whole book.

For `source_type: article`:

- `SKILL.md` — frontmatter as above, the article's thesis, then its key
  claims each with the points supporting it, and a link to the original
  article (the `origin` URL).
- `highlights.md` — the passages worth keeping, as short quotes.

For `source_type: repo`:

- `SKILL.md` — frontmatter as above, what the project does, how to install
  it, the core usage patterns, then a doc index table linking `guides/*.md`.
- `guides/<area>.md` — one per doc area (group segments by topic, not one
  file per source doc): setup, configuration, APIs, workflows — distilled,
  not a file dump.
- `cheatsheet.md` — commands and code snippets from across the docs.

## Step 6 — Verify

Do not trust that generation "looked done":

1. Every file promised by the SKILL.md index exists and is non-empty.
2. Run: `python3 tools/validate_skill.py <install-dir>/<slug>` — must print
   `OK: skill is valid`. Fix any FAIL lines and re-run.
3. For video skills, spot-check one deep link timestamp against
   metadata.json; for playlist skills, spot-check one lesson's video URL.

Then tell the user the skill name, where it was installed, and one example
question to try against it.
