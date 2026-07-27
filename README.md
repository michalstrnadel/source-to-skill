# source-to-skill

**Turn any YouTube video or academic paper into an agent skill — ready to
query while you work in Claude Code, GitHub Copilot CLI, or Amp.**

Watch a 2-hour lecture once, then ask your agent about it forever — and get
answers with timestamp links back into the video. Feed it a paper and get
methods, findings, and limitations as structured files your agent loads on
demand instead of hallucinating.

## How it works

1. **Point** it at a source — `/source-to-skill https://youtube.com/watch?v=...`
   or `/source-to-skill paper.pdf` (arXiv URLs work too).
2. **It extracts** deterministically (yt-dlp / PyMuPDF): transcript with
   chapter timestamps, or paper text with detected sections.
3. **Your agent distills** it into a skill — structure, not summaries:
   frameworks, decision rules, concrete numbers.
4. **Load on demand** — `SKILL.md` stays ~4k tokens; segments and findings
   load only when your question needs them.

## Token math

Pasting a transcript is the expensive way to ask about a video. A 1-hour
talk is roughly 12k words — **~16k tokens** of raw transcript that you pay
on *every* question, and that crowds out the rest of your context. As a
skill, the same talk costs ~4k tokens for `SKILL.md` plus ~1k for the one
segment your question needs — **~5k tokens per question instead of ~16k**,
and it persists across sessions instead of scrolling out of the chat.

## What you get

**From a video:**

    my-lecture/
    ├── SKILL.md          # core ideas + timestamped segment index
    ├── segments/*.md     # per chapter, each deep-linking back (?t=842)
    └── cheatsheet.md     # actionable steps and decision rules

**From a paper:**

    my-paper/
    ├── SKILL.md          # TL;DR + key claims with evidence
    ├── methods.md  findings.md  limitations.md
    ├── glossary.md
    └── citations.md      # ready-to-use citation + reference list

## Install

    git clone https://github.com/michalstrnadel/source-to-skill \
      ~/.claude/skills/source-to-skill
    pip install yt-dlp PyMuPDF   # optional: only what your sources need

Works with any host that supports the open
[Agent Skills](https://github.com/agentskills/agentskills) standard — clone
into `~/.copilot/skills/` or `~/.agents/skills/` instead for Copilot CLI or
Amp. Check your setup with `python3 scripts/extract.py --check`.

## Requirements

- Python ≥ 3.10
- `yt-dlp` for YouTube sources; videos need captions (manual or auto)
- `PyMuPDF` for papers; scanned PDFs without a text layer are not supported yet

## Roadmap

- Whisper fallback for caption-less videos
- OCR for scanned PDFs
- Playlists and multi-source fold-in


Architecture inspired by the excellent MIT-licensed
deterministic-extractor + spec-driven-generator split is their proven design.
All code here is original.

## License

MIT
