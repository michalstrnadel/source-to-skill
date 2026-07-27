# Skills in this repo

| Skill | What it does | Invoke |
|-------|--------------|--------|
| [source-to-skill](source-to-skill/) | Turns a YouTube video or playlist, academic paper (arXiv/PDF), book (EPUB/PDF), web article, or GitHub repo into a structured agent skill with on-demand support files | `/source-to-skill <url-or-file>` |

Each skill folder is self-contained — `SKILL.md` (the agent instructions)
plus any `scripts/` and `tools/` it needs — so it can be installed three
ways:

- **Claude Code plugin:** `/plugin marketplace add michalstrnadel/source-to-skill`, then `/plugin install source-to-skill@source-to-skill`
- **Symlink** (updates via `git pull`): `ln -s "$PWD/skills/source-to-skill" ~/.claude/skills/source-to-skill`
- **Copy** (frozen version): `cp -r skills/source-to-skill ~/.claude/skills/`

The skills that `source-to-skill` *generates* from your sources are not
committed here — they install into your own skills folder.
