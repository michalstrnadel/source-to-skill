https://www.youtube.com/watch?v=zjkBMFhNj_g&t=854s

# 05 — Finetuning into an Assistant

Stage 1 (**pretraining**) gives an internet-document generator — not very
useful for asking questions. Stage 2 (**fine-tuning**) produces an
**assistant model**.

## The recipe

- **Keep the optimization identical** — still next-word prediction.
- **Swap the dataset:** from internet documents to manually collected
  conversations. Companies hire people, give them **labeling instructions**,
  and have them write questions and ideal answers (e.g. a user asks for an
  introduction to "monopsony" in economics; the labeler writes the ideal
  assistant reply).
- The labeling documentation — written by engineers at companies like OpenAI
  or Anthropic — specifies what ideal responses look like.

## Quantity vs quality

| | Pretraining | Fine-tuning |
|---|---|---|
| Data | Tens to hundreds of TB of internet text | E.g. ~100,000 conversations |
| Priority | Quantity, low quality | Quality over quantity |
| Purpose | **Knowledge** | **Alignment** — format change from documents to helpful Q&A |

## What results

- The assistant answers in the style of a helpful assistant even for
  questions not in its fine-tuning set (e.g. "can you help me with this code,
  there's a bug").
- It is remarkable — and empirical, not fully understood — that the model
  changes its *format* to an assistant's while still **using the knowledge
  built during pretraining**.
