# Contributing to source-to-skill

Thanks for wanting to improve source-to-skill. The project turns YouTube
videos and academic papers into agent skills; contributions that make
extraction more robust, generated skills higher-signal, or the docs clearer
are all welcome.

## Development setup

```bash
git clone https://github.com/michalstrnadel/source-to-skill
cd source-to-skill
python3 -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"          # or: pip install pytest yt-dlp PyMuPDF
python3 scripts/extract.py --check   # confirm which extractors you have
```

Python ≥ 3.10. The extractor itself has zero required dependencies —
`yt-dlp` and `PyMuPDF` are optional and only needed for the source types
you actually exercise.

## Running tests

```bash
pytest
```

The suite is fully offline: yt-dlp calls are mocked and the PDF fixture is
generated locally. Keep it that way — no test may hit the network.

## Test-driven changes

Write the failing test first, then the code that makes it pass. Every
behavior change ships with a test; every bug fix ships with a regression
test that fails on the old code. PRs that change parser or validator
behavior without touching `tests/` will be asked for coverage.

Do not trust exit codes when verifying your work — check that
`full_text.txt` and `metadata.json` actually landed and parse, and that
`tools/validate_skill.py` prints `OK: skill is valid` on generated output.

## Commits and pull requests

- One focused change per PR; keep diffs small and reviewable.
- **Conventional Commits** for commit messages and PR titles:
  `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:`, `ci:`, `perf:`
  (e.g. `fix(paper): strip trailing punctuation from DOIs`).
- Update `CHANGELOG.md` for user-visible changes.
- Keep the repo-root `SKILL.md` lean — it is loaded on every run of the
  skill, so net additions to it need a clear justification.

## Proposing a new source type

Open an issue first, covering:

1. **What the source is** and why an agent skill beats pasting it into
   context (token math helps).
2. **The deterministic extraction path** — which library or tool produces
   text plus structure without an LLM and without API keys. Extraction must
   stay deterministic; the distillation is always the user's own agent.
3. **What the segments look like** — how the source maps onto the shared
   `segments` contract (`title`, `start_s`, `pages`, `offset`) and what the
   generated skill's support files should be.

Implementation then touches a known, small surface: a new module in
`scripts/extractor/parsers/`, detection patterns and the optional-dependency
entry in `config.py`, a `detect_source` branch in `utils.py`, a generation
template in `SKILL.md`, and offline tests.

## Where the design lives

The approved v1 design spec and the implementation plan are in
`docs/superpowers/` (`specs/` and `plans/`). Read the spec before proposing
scope changes — v1 boundaries (no Whisper, no OCR, no books) are deliberate,
and the roadmap in the README lists what comes next.
