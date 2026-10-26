---
name: skill-library
description: Your library of skills made by source-to-skill - lists every video, course, podcast, paper, book, article, docs and repo skill installed for Claude Code, Codex, Copilot, Gemini and other agents, finds which one covers a question, flags skills whose playlist, channel, feed or docs has moved on, and refreshes them. Use when the user runs /skill-library, or asks "what skills do I have", "which of my skills covers X", "what did I learn about X", "are any of my skills out of date", "refresh all my skills", or wants to merge overlapping skills.
---

# skill-library

Run from this skill's directory:

    python3 scripts/library.py

It prints JSON: every skill folder with a `source.json` (or, for topic
skills, `sources/*.source.json`) under the agents' user and project skills
folders, with its description, sources, age, and `refresh_due`. It reads
only; pass `--root <dir>` for another folder and `--stale-days N` to change
the 30-day refresh threshold.

## List

Show a compact table: name, type, title, extracted (date), tokens, and a
mark on `refresh_due` skills. Group by source type when there are more than
ten. No skills found → say where you looked and suggest
`/source-to-skill <url-or-file>`.

## Find

For "which skill covers X": match X against each skill's description first,
then open only the matching skills' `SKILL.md` indexes. Answer with the
skill name, the support file, and the deep link or section where X is
covered, then answer the question itself from that file. Name every skill
that covers X when several do; when they disagree, show both positions
side by side.

## Refresh

`refresh_due` marks playlists, channels, podcast feeds, docs sites, repos,
threads and notes folders extracted 30 or more days ago. Before refreshing,
list them with their age and ask which to refresh. For each one the user
picks, follow the source-to-skill skill's "Refresh an existing skill"
steps with that skill directory. Run YouTube re-extractions one at a time,
never in parallel: YouTube rate-limits a machine that asks too often.

## Merge

When two or more skills cover the same topic (overlapping descriptions,
same author or course), offer to build one topic skill from their
`source.json` origins with `/source-to-skill <source> <source> ... <slug>`.
The old skills stay until the user deletes them; never delete a skill
yourself.
