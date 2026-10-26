---
name: skill-eval
description: Measure how well a generated knowledge skill answers questions about its source - grounded questions drafted from the original source, answered using only the skill, graded expectation by expectation, with a score, the facts the skill is missing, and an optional fix. Writes evals/evals.json in the skill-creator format. Use when the user runs /skill-eval, or asks "is this skill any good", "test / evaluate / benchmark my skill", "what did the skill miss", or wants to check a skill made by source-to-skill before relying on it.
---

# skill-eval

Check a skill against the source it was made from. The question is not
"does the skill read well" but "can an agent holding only this skill
answer what the source answers, and cite it correctly".

Usage: `/skill-eval <skill-dir>` (a path, or a skill name found under
`~/.claude/skills/`, `~/.agents/skills/`, `~/.copilot/skills/` or the
project's `.claude/skills/`, `.agents/skills/`, `.github/skills/`).

## Step 1 — Get the questions

If `<skill-dir>/evals/evals.json` exists (source-to-skill writes one while
the source is still in context), use it. Otherwise draft one:

1. Read `<skill-dir>/source.json` (topic skills: `sources/*.source.json`).
   Missing → say the skill was not made by source-to-skill and ask for the
   original source.
2. Re-extract the source with the source-to-skill extractor into a fresh
   work dir (`python3 scripts/extract.py "<source>" [options from the
   manifest] --work-dir <tmp>/skill_eval`, run from the source-to-skill
   skill folder). Tell the user the `est_tokens` and ask before reading it.
3. Draft 8 questions from `full_text.txt`, never from the skill, spread
   across the source's segments: 3 concrete facts or numbers, 2 decision
   rules or "when should I", 2 that need two segments combined, and for
   video or audio 1 "where in the source is X" that needs a timestamp.
   Each gets 1 to 3 expectations: short statements a grader can check
   against an answer, each naming its segment.

Write it in the skill-creator format so the same file works there:

```json
{
  "skill_name": "<slug>",
  "evals": [
    {"id": 1, "prompt": "What learning-rate schedule did the paper use?",
     "expected_output": "Linear warmup for 4000 steps, then inverse square root decay",
     "files": [],
     "expectations": ["States warmup_steps = 4000 (segment 5.3 Optimizer)",
                      "Says the rate then decays proportionally to step^-0.5"]}
  ]
}
```

## Step 2 — Answer with only the skill

The answers must come from someone who has not read the source. If your
host can run subagents, give one subagent the skill directory path and the
eight prompts, and tell it to answer from those files only, citing file
names and deep links. Without subagents, answer them yourself, reading only
the skill's files, and say in the report that grading was not blind.

## Step 3 — Grade

For each expectation: pass or fail, with one line of evidence quoted from
the answer. Also fail an answer whose citation points at the wrong file or
whose timestamp is more than 60 seconds off the moment the source covers
it. Score = passed expectations / all expectations.

Save `<skill-dir>/evals/last-run.json`:
`{"date": "...", "score": 0.83, "results": [{"id": 1, "passed": [true, false], "evidence": ["...", "..."]}]}`.

## Step 4 — Report and fix

Report the score, then each failure as one line: what the source says,
which skill file should have carried it. Separate two causes: the fact is
missing from the skill, or it is there but the index in `SKILL.md` did
not lead to it. Offer to fix both — add the missing facts to the right
support file, sharpen the index line or the description — then re-run only
the failed questions. Change nothing without the user's yes, and run
`python3 tools/validate_skill.py <skill-dir>` (from the source-to-skill
folder) after any edit.
