---
name: skill-study
description: Study a skill made by source-to-skill (a video, course, podcast, paper, book, article or docs skill) - quizzes one question at a time with spaced repetition, Feynman-style "explain it back" checks, a study plan over the lessons, and Anki flashcard export. Every answer cites the skill file and, for video and audio, the exact second. Use when the user says /skill-study, "quiz me on", "test me on", "flashcards from", "help me learn / remember", "study plan for", or "make Anki cards" about a source they turned into a skill.
---

# skill-study

Turn a skill made by source-to-skill into active recall. The skill's files
are the only ground truth: never quiz on, or correct with, facts that are
not in them.

Usage:

- `/skill-study <skill>` — quiz (default mode), due cards first.
- `/skill-study <skill> explain` — the user explains a concept, you check it.
- `/skill-study <skill> plan` — a study plan over the lessons or chapters.
- `/skill-study <skill> anki` — export flashcards for Anki.

`<skill>` is a path or a skill name. Find a name under `~/.claude/skills/`,
`~/.agents/skills/`, `~/.copilot/skills/`, then the project's
`.claude/skills/`, `.agents/skills/`, `.github/skills/`. Several matches or
none: list what you found and ask.

## Ground rules

- Read `SKILL.md` first, then only the support files the current question
  needs (`segments/`, `lessons/`, `chapters/`, `guides/`, `cheatsheet.md`).
- One question per turn. Wait for the answer before showing anything.
- Grade honestly: correct, partly correct (say what was missing), or wrong.
  Then give the answer in two or three sentences with its citation:
  `segments/03-training.md` plus the `&t=` deep link or `[hh:mm:ss]` when
  the file has one.
- Ask for understanding, not trivia: why a rule holds, when a technique
  applies, what a number implies, how two ideas differ. At most one in four
  questions may be a bare number or name recall.
- If the user disputes a grade and the skill file supports them, concede.

## Progress and spaced repetition

Keep progress in `<skill>/.study/progress.json` (create it on first use):

```json
{
  "cards": [
    {"id": "c1", "q": "...", "a": "...", "source": "lessons/02-gradient-descent.md",
     "link": "https://www.youtube.com/watch?v=IHZwWFHWa-w&t=212s",
     "box": 1, "due": "2026-10-27", "seen": 1, "correct": 0}
  ],
  "sessions": [{"date": "2026-10-26", "asked": 8, "correct": 6}]
}
```

Leitner boxes: a correct answer moves the card up one box, a wrong one back
to box 1. Next due date by box: 1 → tomorrow, 2 → 3 days, 3 → 7 days,
4 → 14 days, 5 → 30 days. A quiz asks due cards first, then new cards
from files not yet covered, spreading across the whole skill rather than
the first file. Default length: 8 questions, or what the user asks for.
End with the score, the weakest topic, and when the next cards are due.

## Explain mode

Ask the user to explain one core idea from `SKILL.md` in their own words.
Compare their explanation against the skill: name what was right, what was
missing, and any misconception, each tied to a file. Then ask one follow-up
question that probes the gap. Record the concept as a card in box 1 when
the explanation missed something important.

## Plan mode

From the lesson, chapter or segment index, propose sessions of about 25
minutes: which files to read (or which timestamps to rewatch), in what
order, with the quiz focus for each. Respect the course order for
playlists; for books, start from the chapters the core mental models come
from. Write it to `<skill>/.study/plan.md` only if the user wants it kept.

## Anki export

Write `<skill>/.study/flashcards.tsv` — one card per line, tab-separated,
no header: `front<TAB>back<TAB>tags`. The back ends with the citation and,
when there is one, the deep link as an HTML link
(`<a href="...">03-training 14:02</a>`). Tags: the skill name plus the
lesson or chapter slug. 20 to 40 cards across the whole skill unless the
user asks otherwise; no duplicates of cards already in `progress.json`.
Tell the user to import it in Anki with File → Import, fields separated by
Tab, "Allow HTML in fields" on.
