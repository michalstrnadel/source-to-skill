# Skills in this repo

| Skill | What it does | Invoke |
|-------|--------------|--------|
| [source-to-skill](source-to-skill/) | Turns a YouTube video, playlist or channel, podcast or audio file (local Whisper), academic paper (arXiv/PDF), book (EPUB/PDF), web article, GitHub repo, docs site (llms.txt), notes folder, Word/PowerPoint file, HN/Reddit thread, or meeting transcript, or several at once, into a structured agent skill with on-demand support files; refreshes skills later | `/source-to-skill <url-or-file>` · `/source-to-skill update <skill-dir>` |
| [skill-study](skill-study/) | Quizzes you on a generated skill with spaced repetition, checks explanations, plans study sessions, exports Anki cards | `/skill-study <skill> [explain\|plan\|anki]` |
| [skill-eval](skill-eval/) | Scores a generated skill blind against grounded questions from its source and lists what it misses | `/skill-eval <skill>` |
| [skill-library](skill-library/) | Lists, searches and refreshes every skill source-to-skill made, across all agents' folders | `/skill-library` |

Each skill folder is self-contained — `SKILL.md` (the agent instructions)
plus any `scripts/` and `tools/` it needs — so it can be installed several
ways:

- **Claude Code plugin:** `/plugin marketplace add michalstrnadel/source-to-skill`, then `/plugin install source-to-skill@source-to-skill`
- **Symlink** (updates via `git pull`): `ln -s "$PWD/skills/source-to-skill" ~/.claude/skills/source-to-skill`
- **Copy** (frozen version): `cp -r skills/source-to-skill ~/.claude/skills/`
- **Skills CLI:** `npx skills add michalstrnadel/source-to-skill` (any agent)
- **uv:** `uvx source-to-skill install` (`--agent claude|codex|copilot|gemini|cursor|...`, `--project`, `--only`)

As a plugin, commands are namespaced: `/source-to-skill:skill-study`.

The skills that `source-to-skill` *generates* from your sources install
into your own skills folder. A gallery of generated examples lives in
[`examples/`](../examples/).
