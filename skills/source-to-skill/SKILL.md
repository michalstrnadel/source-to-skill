---
name: source-to-skill
description: Turn a YouTube video, playlist or channel, podcast or audio/video file (local Whisper), academic paper (PDF / arXiv URL), book (EPUB, or PDF book via --type book), web article, GitHub repository, documentation site (llms.txt), Obsidian or Markdown notes folder, Word or PowerPoint file, Hacker News or Reddit thread, or meeting transcript (.srt/.vtt) - or several of them at once - into an installable agent skill, and refresh such skills later. Use when the user runs /source-to-skill, or asks to convert a video, talk, lecture, podcast, episode, recording, playlist, course, channel, paper, PDF, book, EPUB, article, blogpost, GitHub repo, docs site, llms.txt, notes, vault, document, slide deck, discussion thread, or meeting transcript into a skill / structured reference, to merge sources into one topic skill, or to update a skill made from a playlist, channel, feed or docs site.
---

# source-to-skill

Turn a knowledge source into a structured agent skill the user can load on
demand. Supported sources: YouTube video, playlist and channel URLs,
podcasts and audio/video (Apple Podcasts, direct media URLs, local files,
any yt-dlp site via `--type audio`), arXiv URLs, local PDF papers, books
(EPUB files, or PDF books via `--type book`), web article URLs, GitHub
repository URLs, documentation sites (llms.txt), local notes folders,
Word/PowerPoint/OpenDocument files, Hacker News and Reddit threads, and
`.srt`/`.vtt` transcripts.

Usage:

- `/source-to-skill <url-or-file> [skill-slug]` — one source, one skill.
- `/source-to-skill <source> <source> ... [skill-slug]` — several sources,
  one topic skill (see "Several sources" below).
- `/source-to-skill update <skill-dir>` — refresh a skill (see "Refresh").

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
- Channel URLs (`youtube.com/@handle`, `/channel/...`) extract as a
  playlist of the latest 20 uploads (`metadata.json` has
  `"kind": "channel"`); pass `--limit N` for more or fewer. `--limit` also
  caps a long playlist.
- Podcast RSS feeds (`feeds.*` hosts, URLs ending in `.rss`, `.xml`,
  `/feed`, `/rss`) extract as a playlist of the latest 5 episodes
  (`"kind": "feed"`), each transcribed with Whisper — say how many
  episodes and that each takes minutes; `--limit N` changes the count.
- Videos without captions are transcribed locally with Whisper when a
  backend is installed (`--transcribe` forces it even with captions).
  Apple Podcasts links, direct `.mp3`/`.m4a`/... URLs, and local audio or
  video files are detected as `audio` and always transcribed; any other
  page with a video or audio track (Vimeo, SoundCloud, TED, ...) needs
  `--type audio`. Transcription takes a few minutes per hour of audio —
  say so before starting. A different model can be set with the
  `SOURCE_TO_SKILL_WHISPER_MODEL` environment variable.
- Bare `github.com/<owner>/<repo>` URLs are detected as repos (deeper
  paths are not); any other `http(s)` URL is treated as a web article.
- Documentation sites: URLs ending in `/llms.txt` or `/llms-full.txt` are
  detected as `docs`. For any other docs URL (`https://docs.example.com`),
  add `--type docs` — the extractor looks for `llms-full.txt`, then
  `llms.txt`, under the URL's path and at the site root, and fails with a
  hint when the site publishes neither (then offer `--type article` for a
  single page, or the docs' GitHub repo). Linked pages are fetched one by
  one (up to 150); pages that fail are skipped with a stderr warning and
  listed in `metadata.json` under `skipped` — report them to the user,
  and the pages listed under `dropped` (page or text cap) too.
- A local folder (an Obsidian vault, a Markdown notes or docs folder,
  Logseq's `pages/`) is detected as `notes`. Hidden folders (`.obsidian`,
  `.git`, `.trash`) and binary or oversized files are skipped; report
  notes listed under `dropped` in `metadata.json` to the user. These are
  the user's private notes: confirm the folder and what the skill is for
  before generating, and keep the skill local (never suggest publishing
  it) unless the user says otherwise.
- Hacker News items (`news.ycombinator.com/item?id=N`) and Reddit posts
  (`reddit.com/r/<sub>/comments/<id>/...`, `old.`/`np.` hosts,
  `redd.it/<id>`) are detected as `thread`. Very large threads are cut at
  a comment cap with a stderr note: say so, comparing `comments_extracted`
  with `num_comments`. If Reddit answers HTTP 403 (some networks block
  anonymous access), report the error verbatim and stop.
- Local `.docx`, `.pptx`, `.odt` and `.odp` files are detected as
  `document`; old binary `.doc`/`.ppt` files need re-saving first (the
  error says so). Local `.srt` and `.vtt` files (Zoom/Teams/Meet meeting
  exports, downloaded captions) are detected as `transcript` and need no
  transcription.
- On dependency errors, run `python3 scripts/extract.py --check` and show the
  user the install hints. Do not install anything without asking.
- On any other ERROR, report it verbatim and stop.
- On success the command prints JSON with `work_dir`, `title`, `est_tokens`,
  and `segments`. All extracted content is in `<work_dir>/full_text.txt` and
  `<work_dir>/metadata.json`; `<work_dir>/source.json` records what was
  extracted so the skill can be refreshed later.

## Step 2 — Confirm cost

Tell the user the title, source type, and `est_tokens`, and ask to proceed.
Generation reads the full text once; skills built from it cost a fraction of
that per future question.

## Step 3 — Analyze structure

Read `metadata.json`. For large sources (over ~40k est_tokens) do NOT read
`full_text.txt` in one go — read it segment by segment using the `offset`
values (character offsets, not bytes; each segment's text runs to the next
segment's offset). Above ~100k est_tokens, if your host can run subagents,
hand each one a range of segments to distill and assemble the results
yourself.

## Step 4 — Choose install target

Ask the user where to install (default first):

1. `~/.claude/skills/<slug>/` (Claude Code, user-level)
2. `~/.agents/skills/<slug>/` (cross-agent: Codex, Cursor, Gemini CLI,
   Copilot, Amp, OpenCode, Goose, Factory)
3. `~/.copilot/skills/<slug>/` (GitHub Copilot CLI)
4. `./.claude/skills/<slug>/` (this project only, Claude Code)
5. `./.agents/skills/<slug>/` (this project only, cross-agent)
6. `./.github/skills/<slug>/` (this project only, GitHub Copilot)

Another folder the user names (`~/.gemini/skills/`, `~/.cursor/skills/`,
`~/.kiro/skills/`, ...) is fine too.

`<slug>` is the second argument if given, else slugified from the title.

## Step 5 — Generate

Always write in English, regardless of source language. Extract structure —
frameworks, decision rules, anti-patterns, concrete numbers — never padded
summaries. Front-load the most important content in SKILL.md and keep it
under ~4k tokens; support files carry the detail.
A support file must carry content SKILL.md does not; for a small source
(under ~3k est_tokens) skip files that would only repeat it. Short quotes
(two sentences at most) are fine in any skill; never long passages.

In `full_text.txt`, `| a | b |` lines are tables (keep them as tables),
`[image: ...]` and `[figure] ...` lines stand for images that were not
extracted, and repo segments flagged `"orphan"` or `"stub"` rarely
deserve their own file.

When `metadata.json` says `"captions": "auto"`, the transcript is machine
captions: fix names that are unambiguously misheard (a model, a person,
a product the context makes certain) and leave anything uncertain
generic — never guess a fact.

For `source_type: youtube`:

- `SKILL.md` — frontmatter (name = slug; description = what the video
  teaches and when to load this skill), core ideas, then a segment index
  table: segment title, one-line takeaway, link `segments/NN-<slug>.md`.
- `segments/NN-<slug>.md` — one per segment, first line is the deep link
  `<origin>&t=<start_s>s` (use `?t=` if the origin URL has no query string),
  then the distilled content of that segment. Merge segments under ~60
  seconds into their neighbour. Inline `[t=Ns]` markers in the text mark
  moments inside a segment — use them to link a specific claim or quote
  to its own second, not just the segment start. Segment boundaries can
  split a sentence; attach the fragment to the segment it belongs to.
- `cheatsheet.md` — actionable steps, decision rules, and named techniques
  from the whole video.

For `source_type: audio` (a podcast episode, talk, or recording): the same
files as a video. Each segment file opens with
`deep_link_template` with `{s}` replaced by `start_s` when that field is
not null, otherwise with the `[hh:mm:ss]` timestamp and the `origin`.
SKILL.md names the show or speaker (`channel`) and, for conversations,
attributes claims to who made them when the transcript makes it clear.

For `source_type: playlist` (a course; `"kind": "channel"` is a channel
and `"kind": "feed"` a podcast show — describe what it covers rather than
a course order):

- `SKILL.md` — frontmatter as above, course overview (what the course
  teaches and in what order), then a lesson index table: lesson, one-line
  takeaway, link `lessons/NN-<slug>.md`.
- `lessons/NN-<slug>.md` — one per video, numbered in playlist order; the
  first line is the video URL (the segment's `url` field), then the
  distilled content of that lesson, linking key moments with the
  segment's `deep_link_template` (`{s}` → seconds from the transcript's
  inline `[t=Ns]` markers; no template → cite `[mm:ss]`).
- If the playlist is not one coherent course (unrelated videos, a part 2
  without its part 1), say so in the overview instead of inventing an
  order.
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
  Segments marked `"front_matter": true` (contents, contributors,
  dedications) get no chapter file; mention a license
  page in one line.
- `glossary.md` — key terms alphabetically, each with a one-line definition
  and the chapter it comes from.
- `cheatsheet.md` — decision rules, named techniques, and anti-patterns
  from the whole book.

For `source_type: article`:

- `SKILL.md` — frontmatter as above, a byline (author and date when
  known — check the text if `metadata.json` has none), the article's
  thesis, then its key claims each with the points supporting it, and a
  link to the original article (the `origin` URL).
- `highlights.md` — the passages worth keeping, as short quotes.

For `source_type: repo`:

- `SKILL.md` — frontmatter as above, what the project does, how to install
  it, the core usage patterns, then a doc index table linking `guides/*.md`.
- `guides/<area>.md` — one per doc area (group segments by topic, not one
  file per source doc): setup, configuration, APIs, workflows — distilled,
  not a file dump.
- `cheatsheet.md` — commands and code snippets from across the docs.

For `source_type: docs` (a documentation site via llms.txt):

- `SKILL.md` — frontmatter as above, what the product or library is (from
  `summary` and the Overview segment), how to install or start, the core
  concepts and usage patterns, then a doc index table: area, what it
  covers, link `guides/<area>.md`, and the original page URLs (segment
  `url`) so answers can cite the live docs.
- `guides/<area>.md` — one per doc area (follow each segment's llms.txt
  `section`, merging small sections and splitting very large ones by
  topic): concepts, configuration, APIs, workflows — distilled, not a page
  dump. Each guide lists the source page URLs it draws on. Segments marked
  `"optional": true` are secondary: fold them in only where they add
  something.
- `cheatsheet.md` — commands, config keys, API calls and code snippets
  from across the docs, each with its page URL.

For `source_type: notes` (the user's own notes folder):

- `SKILL.md` — frontmatter as above, the user's own frameworks, principles
  and recurring ideas front-loaded (in their words, not generic advice),
  then an index of hub notes (`hubs` in metadata.json, plus notes with
  many `links`): title, one-line gist, link `topics/<slug>.md`.
- `topics/<slug>.md` — one per hub note, folder, or tag cluster (`tags`),
  loaded on demand: the ideas, how they connect (via `links`), and the
  note paths (`path`) they come from — distilled, not copied.
- `decisions.md` — decisions the user has recorded (with their reasons and
  dates when the notes give them) and open questions still unresolved,
  each with its note path.
- Privacy: include only what serves the purpose the user stated. Never
  copy credentials, personal data about other people, health, financial
  or journal-style private entries, or long verbatim passages; when unsure
  whether a note belongs in the skill, ask. Reference notes by relative
  `path`, never by absolute path.

For `source_type: document` (`format` `docx`/`odt` is a written document,
`pptx`/`odp` a slide deck):

- `SKILL.md` — frontmatter as above, a byline (`author`, `date` when
  known), what the document is for (decision memo, spec, handbook, pitch),
  its key points, decisions and numbers front-loaded, then a section index
  table: section (or slide range), one-line takeaway, link
  `sections/NN-<slug>.md`. Under ~3k est_tokens, put everything here.
- `sections/NN-<slug>.md` — one per section in document order. For decks,
  group consecutive slides on one topic (cite each segment's `slide`).
  `Notes:` lines are speaker notes and often hold the real argument behind
  terse bullets: distill them with the slide, never drop them. Skip
  segments flagged `"hidden": true` unless they carry unique content.

For `source_type: thread` (a Hacker News or Reddit discussion):

- `SKILL.md` — frontmatter as above (description = the question or topic
  and when to load this skill), the post in one or two sentences linking
  `origin` and `linked_url` (when not null), the consensus and how strong
  it is, and the strongest arguments on each side, each attributed to its
  commenter with a link to the comment (the segment's `url`). Votes and
  reply depth show weight, not truth: a well-argued minority point
  outranks a popular quip.
- `tips.md` — concrete tips, numbers, benchmarks, tools and war stories,
  each with the commenter and the segment `url`; mark claims disputed in
  their replies.
- `dissent.md` — minority views and objections as stated, with who holds
  them — never averaged into the consensus; note disagreements the thread
  never resolved.
- Ignore jokes, meta-discussion and off-topic subthreads. Indented lines
  are replies; a line without an `author:` prefix continues the comment
  above it.

For `source_type: transcript` (a local `.srt`/`.vtt`, usually a meeting;
a talk or lecture gets the `audio` template instead):

- `SKILL.md` — frontmatter as above (description = what the meeting
  decided and when to load this skill), purpose and participants
  (`speakers`), then decisions (who made or confirmed each, with its
  `[hh:mm:ss]` from the `[t=Ns]` markers), action items (owner, task,
  deadline when stated — otherwise "owner unclear", never invented), and
  open questions.
- `speakers.md` — each participant's positions, proposals, objections and
  commitments with timestamps; disagreements stay attributed, not merged.
- `segments/NN-<slug>.md` — only for meetings over ~30 minutes: one per
  10-minute part, opening with its `[hh:mm:ss]` start. Machine transcripts
  mishear names and jargon: fix only what the context makes certain.

Every single-source skill: copy `<work_dir>/source.json` into the skill
directory unchanged, so it can be refreshed later.

Every skill: while the source is still in context, write
`evals/evals.json` — 6 questions the source answers, drafted from the
source, not from what you wrote: 2 concrete facts or numbers, 2 decision
rules, 1 that combines two segments, and for video or audio 1 that needs a
timestamp. Each has `id`, `prompt`, `expected_output`, `files: []`, and
1 to 3 checkable `expectations` naming the segment, under
`{"skill_name": "<slug>", "evals": [...]}` (the skill-creator format).
The skill-eval skill grades the skill against them later.

## Step 6 — Verify

Do not trust that generation "looked done":

1. Every file promised by the SKILL.md index exists and is non-empty.
2. Run: `python3 tools/validate_skill.py <install-dir>/<slug>` — must print
   `OK: skill is valid`. Fix any FAIL lines and re-run.
3. For video skills, spot-check one deep link timestamp against
   metadata.json; for playlist skills, spot-check one lesson's video URL.

Then tell the user the skill name, where it was installed, and one example
question to try against it. Mention once that `/skill-eval <slug>` scores
the skill against its `evals/evals.json` and `/skill-study <slug>` quizzes
them on it, when those skills are installed.

## Several sources → one topic skill

When the user passes more than one source (or asks to merge sources on one
topic):

1. Extract each into its own work dir:
   `python3 scripts/extract.py "<source>" --work-dir <tmp>/source_skill_topic/NN`
   (NN = 01, 02, ... in the order given). Report failures per source and
   continue with the rest only if the user agrees.
2. Confirm cost once, with the sum of `est_tokens` and one line per source.
3. Generate (slug = given, else from the shared topic):
   - `SKILL.md` — frontmatter as above; the synthesized core ideas, each
     tagged with the sources that support it (`[S1]`, `[S2]`); then a
     sources table: id, title, type, one-line takeaway, link
     `sources/NN-<slug>.md`.
   - `sources/NN-<slug>.md` — one per source, the first line its origin:
     that source type's content condensed into one file, with the files
     its template would create as `##` sections (deep links and
     timestamps included).
   - `disagreements.md` — where sources contradict each other, use
     different definitions, or give different numbers: each point states
     both positions with their source ids. Never average them into one
     claim. If they agree throughout, say so in one line.
   - `cheatsheet.md` — actionable steps across all sources, each tagged
     with its source ids.
   - Copy each work dir's `source.json` to `sources/NN-<slug>.source.json`
     (topic skills have no top-level `source.json`; refresh one source by
     re-extracting it and comparing against its own manifest).
4. Verify as in Step 6.

## Refresh an existing skill

For `/source-to-skill update <skill-dir>` (most useful for playlists and
channels that keep growing):

1. Read `<skill-dir>/source.json`. Missing → the skill predates refresh
   support; tell the user and stop.
2. Re-extract the same source with the same options into a fresh dir:
   `python3 scripts/extract.py "<source>" [--type T] [--limit N] [--transcribe] --work-dir <tmp>/source_skill_update`
   using the manifest's `source` and `options`.
3. Run `python3 tools/diff_source.py <skill-dir> <tmp>/source_skill_update`.
   No `added` entries → tell the user the skill is up to date and stop.
4. Show the added (and removed) items with the new `est_tokens`, ask to
   proceed, then generate only the added lessons/segments (number new
   files by their `position`), add them to the SKILL.md index, extend the
   cheatsheet, and leave existing files untouched. Never delete files for
   removed items — list them for the user instead.
5. Replace `<skill-dir>/source.json` with the new one and verify as in
   Step 6.
