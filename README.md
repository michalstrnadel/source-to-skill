<p align="center">
  <img src="docs/assets/logo.png" alt="source-to-skill logo" width="120">
</p>

<h1 align="center">source-to-skill</h1>

<p align="center">
  <strong>Turn YouTube videos, academic papers, and books into agent skills — watch a lecture, read a paper, or finish a book once, then query it forever from Claude Code, GitHub Copilot CLI, or Amp.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/License-MIT-blue?style=for-the-badge" alt="MIT License">
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/Agent_Skills-Open_Standard-blueviolet?style=for-the-badge" alt="Agent Skills open standard">
  <img src="https://img.shields.io/badge/YouTube%20%E2%80%A2%20PDF%20%E2%80%A2%20arXiv%20%E2%80%A2%20EPUB-supported-green?style=for-the-badge" alt="YouTube, PDF, arXiv and EPUB supported">
  <img src="https://img.shields.io/badge/PRs-welcome-brightgreen?style=for-the-badge" alt="PRs welcome">
</p>

<p align="center">
  <a href="#why">Why</a> ·
  <a href="#how-it-works">How it works</a> ·
  <a href="#what-it-generates">What it generates</a> ·
  <a href="#usage">Usage</a> ·
  <a href="#requirements">Requirements</a> ·
  <a href="#faq">FAQ</a> ·
  <a href="#roadmap">Roadmap</a> ·
  <a href="#architecture">Architecture</a>
</p>

<p align="center">
  <strong>~5,000 tokens per question instead of ~16,000</strong> for a one-hour talk —
  and every answer deep-links back to the exact timestamp (<a href="#token-math">how it's counted</a>).
</p>

<!-- Demo GIF coming soon: /source-to-skill on a lecture URL → generated skill → agent answering with a &t= timestamp deep link. Drop the recording at docs/assets/demo.gif and embed it here. -->

---

## Why

You watch a brilliant two-hour lecture. Three weeks later all you remember is that one diagram — and no idea at which minute it appeared. Papers are worse: you *know* the answer is in there somewhere. And that great technical book you finished last spring? You can't remember chapter 7 existed.

The usual workarounds fail in familiar ways:

- "I'll rewatch the relevant part" → you scrub through two hours to find ninety seconds
- "I'll search the PDF" → you get a list of page hits, not an answer
- "I'll ask my AI agent about the paper" → it hallucinates confident details the paper never claimed

**source-to-skill turns YouTube videos, papers, and books into agent skills** — structured references your agent loads on demand and answers from, grounded in the actual transcript, paper, or book text. Ask about the lecture and the answer arrives with a `&t=` link that drops you at the right second of the video. Ask about the paper and you get its real methods, findings, and limitations — not a plausible invention. Ask about the book and the answer comes from the chapter that actually says it.

Because generated skills follow the open [Agent Skills](https://github.com/agentskills/agentskills) standard, one build serves Claude Code, GitHub Copilot CLI, and Amp alike.

---

## How it works

Three steps, one command:

1. **Point** it at a source — `/source-to-skill https://youtube.com/watch?v=...`, `/source-to-skill paper.pdf`, or `/source-to-skill book.epub` (arXiv URLs work too; a PDF book takes `--type book`).
2. **The extractor runs** — deterministic Python, no LLM involved: `yt-dlp` pulls captions and chapter timestamps from the video, `PyMuPDF` pulls text and detected sections from the paper, or the standard library unpacks an EPUB into its ordered chapters.
3. **Your agent distills** the extracted text into a skill by following this repo's `SKILL.md` — it pulls out the frameworks, the decision rules, the hard numbers, and anchors each one to its timestamp or section. What lands on disk is a structured reference, not a condensed retelling.

The split matters: **extraction is deterministic code, distillation is your own agent**. There is no API key, no cloud service, and no second model — the AI agent you already run does the thinking, and the extractor guarantees it thinks about the real content.

From then on, the generated video, paper, and book skills behave like any other skill: `SKILL.md` stays resident at ~4k tokens, and segment, findings, or chapter files load only when a question needs them.

---

## What it generates

Running `/source-to-skill <source>` writes a complete skill into your agent's skills directory (`~/.claude/skills/<slug>/` for Claude Code, `~/.copilot/skills/<slug>/` for Copilot CLI, `~/.agents/skills/<slug>/` for Amp or cross-agent use).

**From a YouTube video:**

```
my-lecture/
├── SKILL.md          # core ideas + timestamped segment index
├── segments/
│   ├── 01-intro.md   # each segment opens with its deep link (…&t=0s)
│   ├── 02-attention.md   # …&t=842s — click and land at that second
│   └── …
└── cheatsheet.md     # actionable steps and decision rules
```

| File | Purpose | Size |
|------|---------|------|
| `SKILL.md` | Core ideas + timestamped segment index | ~4,000 tokens |
| `segments/NN-*.md` | One per chapter/segment, loaded on demand, opens with a `&t=` deep link | ~1,000 tokens each |
| `cheatsheet.md` | Actionable steps, decision rules, named techniques | ~1,000 tokens |

**From a paper (local PDF or arXiv URL):**

```
my-paper/
├── SKILL.md          # TL;DR + key claims, each with evidence
├── methods.md        # how the work was done
├── findings.md       # results with concrete numbers and conditions
├── limitations.md    # stated caveats + ones evident from the methods
├── glossary.md       # every key term, one-line definitions
└── citations.md      # ready-to-paste citation + reference list
```

| File | Purpose | Size |
|------|---------|------|
| `SKILL.md` | TL;DR + key claims with supporting evidence | ~3,000 tokens |
| `methods.md` | Enough methodological detail to assess validity | ~1,500 tokens |
| `findings.md` | Results with concrete numbers and conditions | ~1,500 tokens |
| `limitations.md` | Stated limitations plus caveats the methods imply | ~800 tokens |
| `glossary.md` | Terms alphabetically, one-line definitions | ~800 tokens |
| `citations.md` | How to cite + extracted reference list | ~500 tokens |

**From a book (EPUB, or PDF with `--type book`):**

```
my-book/
├── SKILL.md          # core mental models + chapter index
├── chapters/
│   ├── 01-foundations.md   # one per chapter, loaded on demand
│   ├── 02-deliberate-practice.md
│   └── …
├── glossary.md       # key terms with chapter references
└── cheatsheet.md     # decision rules, techniques, anti-patterns
```

| File | Purpose | Size |
|------|---------|------|
| `SKILL.md` | Core mental models + chapter index table | ~4,000 tokens |
| `chapters/NN-*.md` | One per chapter, loaded on demand | ~1,000 tokens each |
| `glossary.md` | Key terms alphabetically, each with its chapter reference | ~800 tokens |
| `cheatsheet.md` | Decision rules, named techniques, anti-patterns | ~1,000 tokens |

Support files load on demand — they cost nothing until a question needs them.

---

## Usage

```
/source-to-skill <url-or-file> [skill-slug]
```

**Examples:**

```bash
# Turn a YouTube video into an agent skill
/source-to-skill https://www.youtube.com/watch?v=dQw4w9WgXcQ

# Turn an arXiv PDF into a Claude Code skill, straight from the URL
/source-to-skill https://arxiv.org/abs/1706.03762

# Local PDF paper
/source-to-skill ~/papers/attention-is-all-you-need.pdf

# EPUB book — auto-detected, no extra dependency needed
/source-to-skill ~/books/deep-work.epub

# A book that ships as PDF — tell the extractor it's a book, not a paper
/source-to-skill ~/books/algorithm-design.pdf --type book

# Pick your own skill slug
/source-to-skill https://youtu.be/dQw4w9WgXcQ transformer-lecture
```

Once installed, query it like any other skill:

```bash
/transformer-lecture                          # load the core ideas
/transformer-lecture "what was said about positional encoding?"
/my-paper "what dataset did they evaluate on?"
```

Video answers come with `&t=` links that jump you to the exact moment; paper answers cite the section they came from.

### Install

Clone into the skills folder of whichever agent you use — same repo, three homes:

```bash
# Claude Code
git clone https://github.com/michalstrnadel/source-to-skill ~/.claude/skills/source-to-skill

# GitHub Copilot CLI
git clone https://github.com/michalstrnadel/source-to-skill ~/.copilot/skills/source-to-skill

# Amp / cross-agent
git clone https://github.com/michalstrnadel/source-to-skill ~/.agents/skills/source-to-skill
```

Then install only what your sources need:

```bash
pip install yt-dlp     # for YouTube videos
pip install PyMuPDF    # for PDF papers and PDF books
# EPUB books need nothing extra — the standard library handles them
```

Verify your setup any time with `python3 scripts/extract.py --check` — it reports each optional dependency and the exact install hint for anything missing.

---

## Token math

Pasting a transcript is the expensive way to ask about a video. A one-hour talk is roughly 12k words — **~16k tokens** of raw transcript that you pay on *every* question, crowding out the rest of your context. As a skill, the same talk costs ~4k tokens for the resident `SKILL.md` plus ~1k for the one segment your question touches — **~5k tokens per question instead of ~16k**, and it persists across sessions instead of scrolling out of the chat.

The gap widens with length: the transcript cost grows linearly with the video, while the skill cost stays flat at core-plus-one-segment.

---

## Requirements

Honest constraints, stated up front:

- **Python ≥ 3.10.** The extractor itself has no required dependencies.
- **YouTube videos must have captions.** Manual captions are preferred; auto-generated captions are the fallback. A video with no captions at all fails with a clear error — v1 does **not** transcribe audio (Whisper is on the [roadmap](#roadmap)). Needs `yt-dlp`.
- **PDFs must have a text layer** — papers and PDF books alike. Scanned PDFs are rejected — there is no OCR yet. Needs `PyMuPDF`.
- **EPUB books need no extra dependency.** An EPUB is a zip of XHTML, and the extractor reads it with the Python standard library alone. PDF books use the same PyMuPDF path as papers (pass `--type book`); chapters come from the PDF outline when one exists.
- **arXiv URLs use modern IDs** — `arxiv.org/abs/2406.01234`-style (2007+). Older `math/0605197`-style IDs aren't recognized; download the PDF and pass the file instead.

`python3 scripts/extract.py --check` tells you exactly where you stand.

---

## FAQ

**"Does it transcribe the audio?"**

No. v1 reads the video's captions — manual first, auto-generated as fallback — via `yt-dlp`. If a video has no captions, extraction stops with a clear error rather than guessing. Whisper-based transcription for caption-less videos is a roadmap item.

---

**"What about books, notes, or documentation folders?"**


---

**"Does it need an API key?"**

No. Extraction is plain deterministic Python running on your machine, and the distillation is done by the agent you already run — Claude Code, Copilot CLI, or Amp. No cloud service of ours ever sees your sources.

---

**"Which agents does it work with?"**

Claude Code, GitHub Copilot CLI, and Amp — and anything else built on the open [Agent Skills](https://github.com/agentskills/agentskills) standard. Clone into whichever skills folder your agent watches, and it picks the skill up like any other.

---



---

**"Can't I just paste the transcript into context?"**

You can — once. But you'll pay the full ~16k tokens again on every question, and the transcript scrolls away when the session ends. The skill costs ~5k per question and survives forever. See [Token math](#token-math).

---

## Roadmap

- **Whisper fallback** for caption-less videos
- **OCR** for scanned PDFs without a text layer
- **Playlists** and multi-source fold-in

---

## Architecture

Two halves with a hard boundary — deterministic extraction, agent-driven generation:

```
/source-to-skill <url|pdf|epub> [slug]
        │
        ▼
scripts/extract.py            deterministic Python — no LLM, no API keys
        ├─ YouTube URL ─────────► parsers/youtube.py   (yt-dlp: captions, chapters, timestamps)
        ├─ PDF / arXiv ─────────► parsers/paper.py     (PyMuPDF: text, section detection, references)
        └─ EPUB / --type book ──► parsers/book.py      (stdlib EPUB unzip; PDF outline chapters)
        │
        ▼
<tmp>/source_skill_work/
        ├─ full_text.txt      normalized text, segment-addressable by offset
        └─ metadata.json      shared contract: title, segments, est_tokens
        │
        ▼
Your agent follows SKILL.md   distills structure — frameworks, rules, numbers
        │
        ▼
~/.claude/skills/<slug>/      (or ~/.copilot/skills/, ~/.agents/skills/)
        │
        ▼
tools/validate_skill.py       every promised file exists, frontmatter valid
```

All three parsers emit the same `full_text.txt` + `metadata.json` contract, so the generator never branches on parser internals — a new source type needs a parser, a `SKILL.md` template, and a little wiring ([Extending](docs/ARCHITECTURE.md#extending)), while the contract stays fixed.

```
source-to-skill/
├── SKILL.md                 # the generator spec — this IS the skill
├── scripts/
│   ├── extract.py           # entrypoint: detect source, dispatch, write outputs
│   └── extractor/
│       ├── config.py        # supported sources, paths, optional-dependency map
│       ├── dependencies.py  # optional-dep probing + --check report
│       ├── utils.py         # source detection, slugify, segmentation
│       └── parsers/
│           ├── youtube.py   # yt-dlp: captions, chapters, timestamps
│           ├── paper.py     # PyMuPDF: text, sections, references
│           └── book.py      # EPUB via stdlib; PDF books via outline
├── tools/
│   └── validate_skill.py    # lint a generated skill before you trust it
├── tests/                   # pytest suite — fixtures only, no network
└── docs/superpowers/specs/  # design documents
```

---



## License

MIT — covers this tool. The videos, papers, and books you convert keep their own rights; treat generated skills of third-party content as personal notes and don't redistribute them.
