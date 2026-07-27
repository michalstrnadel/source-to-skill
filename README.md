# <img src="docs/assets/logo.png" width="28" align="top" alt=""> source-to-skill

One command to turn YouTube videos, academic papers, and books into agent skills.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB)](pyproject.toml)
[![Agent Skills](https://img.shields.io/badge/Agent_Skills-Open_Standard-7c3aed)](https://github.com/agentskills/agentskills)
[![Sources](https://img.shields.io/badge/YouTube_%E2%80%A2_PDF_%E2%80%A2_arXiv_%E2%80%A2_EPUB-supported-green)](#requirements)

<!-- Demo GIF: /source-to-skill on a lecture URL → generated skill → agent answering with a &t= timestamp deep link. Drop the recording at docs/assets/demo.gif and embed it here. -->

Point it at a source and your coding agent (Claude Code, GitHub Copilot CLI, Amp — any [Agent Skills](https://github.com/agentskills/agentskills) host) distills it into a structured skill it loads on demand. Video answers deep-link back to the exact `&t=` timestamp, papers keep their methods/findings/limitations structure, books keep their chapters. Everything runs locally through your own agent — no API keys, no cloud.

## Quick start

```bash
git clone https://github.com/michalstrnadel/source-to-skill ~/.claude/skills/source-to-skill
pip install yt-dlp PyMuPDF   # only what your sources need; EPUB needs neither
```

1. In Claude Code: `/source-to-skill https://www.youtube.com/watch?v=...`
2. The agent extracts the source, shows a token estimate, and asks where to install the generated skill.
3. Ask `/your-video-slug <question>` — the answer cites the transcript and links the exact second of the video.

From a two-hour lecture you get something like:

```
attention-explained/
├── SKILL.md              # core ideas + timestamped segment index
├── segments/
│   ├── 01-intro.md       # one per video chapter, loaded on demand,
│   ├── 02-self-attention.md   #   each opening with its &t= deep link
│   └── ...
└── cheatsheet.md         # actionable steps and decision rules
```

Papers and books work the same way — `/source-to-skill https://arxiv.org/abs/1706.03762` yields `methods.md` / `findings.md` / `limitations.md` / `glossary.md` / `citations.md`; `/source-to-skill book.epub` yields a chapter index with on-demand chapter files.

## Features

- **YouTube → skill** — captions via yt-dlp (manual preferred, auto fallback, any language), segmented by the video's own chapters; every segment file deep-links back with `&t=`.
- **Paper → skill** — PyMuPDF extraction with academic section detection; arXiv URLs download automatically.
- **Book → skill** — EPUB parsing with the Python standard library alone; PDF books via `--type book` take chapters from the document outline.
- **Deterministic extractor, agent generator** — Python normalizes every source to one text + metadata contract; your agent does the distillation following `SKILL.md`. Skills are structure (frameworks, decision rules, concrete numbers), not summaries.
- **Cheap to query** — the generated `SKILL.md` stays around 4k tokens; segment, chapter, and findings files load only when a question needs them.

## Requirements

- Python ≥ 3.10
- `yt-dlp` for YouTube, `PyMuPDF` for PDFs — install only what you use; EPUB has no extra dependency
- Videos need captions (manual or auto-generated); audio transcription is on the roadmap
- Scanned PDFs without a text layer are not supported (OCR is on the roadmap)

Check your setup anytime:

```bash
python3 scripts/extract.py --check
```

## Install for other agents

Clone into the skills folder your agent reads:

```
~/.claude/skills/    # Claude Code
~/.copilot/skills/   # GitHub Copilot CLI
~/.agents/skills/    # Amp / cross-agent
```

Project-local `.claude/skills/`, `.agents/skills/`, or `.github/skills/` work too.

## How it works

`scripts/extract.py` detects the source type (YouTube URL, arXiv URL, local PDF or EPUB, with an optional `--type` override), parses it with the matching parser, and writes normalized `full_text.txt` + `metadata.json` to a work directory. Your agent then follows the repo-root `SKILL.md`: it confirms the token cost with you, distills the text through the template for that source type, installs the skill where you choose, and validates the result with `tools/validate_skill.py`. Details in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Troubleshooting

- **"No captions available"** — the video has no manual or auto captions; transcription isn't supported yet.
- **"no usable text layer (scanned PDF?)"** — the PDF is image-only; run it through OCR first.
- **"Missing dependency"** — run `python3 scripts/extract.py --check` and install what it suggests.
- **A PDF book parsed as a paper** — PDFs default to the paper parser; pass `--type book` to use the book parser with outline chapters.
- **Wrong chapters on a PDF book** — the PDF has no outline; the parser falls back to heading detection, then full text.

## License

[MIT](LICENSE)
