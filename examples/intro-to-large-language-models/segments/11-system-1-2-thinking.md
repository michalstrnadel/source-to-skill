https://www.youtube.com/watch?v=zjkBMFhNj_g&t=2100s

# 11 — Thinking: System 1 vs System 2

(Future directions the field is interested in — explicitly *not* OpenAI
product announcements.)

## The distinction (from *Thinking, Fast and Slow*)

| | System 1 | System 2 |
|---|---|---|
| Character | Quick, instinctive, automatic | Rational, slower, effortful, conscious |
| Arithmetic | 2 + 2 = 4 (cached) | 17 × 24 (must work it out) |
| Chess | Speed chess: moves that "look right" | Competition: lay out and maintain a tree of possibilities |

## Where LLMs stand (Nov 2023)

- LLMs currently have **only System 1**: words go in, the network outputs the
  next word, "chunk, chunk, chunk" — each chunk takes roughly the same time.
  They cannot reason through a tree of possibilities.

## The goal: convert time into accuracy

- You should be able to say: "here's my question, take 30 minutes, I don't
  need the answer right away."
- Plot time (x) against accuracy (y): we want a **monotonically increasing**
  curve. At the time no model had this.
- Research direction: build a **tree of thoughts** — think, reflect,
  rephrase, then return a more confident answer.
