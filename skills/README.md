# Skills in this repo

| Skill | What it does | Invoke |
|-------|--------------|--------|
| [source-to-skill](source-to-skill/) | Turns a YouTube video, playlist or channel, podcast or audio file (local Whisper), academic paper (arXiv/PDF), book (EPUB/PDF), web article, or GitHub repo, or several at once, into a structured agent skill with on-demand support files; refreshes skills later | `/source-to-skill <url-or-file>` · `/source-to-skill update <skill-dir>` |

Each skill folder is self-contained — `SKILL.md` (the agent instructions)
plus any `scripts/` and `tools/` it needs — so it can be installed three
ways:

- **Claude Code plugin:** `/plugin marketplace add michalstrnadel/source-to-skill`, then `/plugin install source-to-skill@source-to-skill`
- **Symlink** (updates via `git pull`): `ln -s "$PWD/skills/source-to-skill" ~/.claude/skills/source-to-skill`
- **Copy** (frozen version): `cp -r skills/source-to-skill ~/.claude/skills/`
- **PyPI:** `uvx source-to-skill install` (`--agent claude|agents|copilot`, `--project`)

The skills that `source-to-skill` *generates* from your sources install
into your own skills folder. A gallery of generated examples lives in
[`examples/`](../examples/).
