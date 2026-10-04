https://www.youtube.com/watch?v=zjkBMFhNj_g&t=1663s

# 09 — Tool Use (browser, calculator, interpreter, DALL-E)

Capabilities explained via one concrete ChatGPT session about Scale AI.

## The demo, step by step

| Step | Prompt (paraphrased) | Tool | Result |
|---|---|---|---|
| 1 | Collect Scale AI's funding rounds: date, amount, valuation; make a table | **Browser** (Bing search) | Table of Series A–E with citation links; valuations for A and B not found ("not available") |
| 2 | Impute A and B valuations from the ratios in C, D, E | **Calculator** | ~$70M and ~$283M |
| 3 | 2D plot: x = date, y = valuation, log scale, grid lines, professional | **Python interpreter** (matplotlib) | The plot |
| 4 | Add a linear trend line, extrapolate to end of 2025, vertical line at today, report values | Python | ~$150B "today", ~$2T by end of 2025 (said tongue-in-cheek) |
| 5 | Generate an image representing Scale AI, based on the context above | **DALL-E** | An image |

## How it works

- Fine-tuning teaches the model that for certain queries it should **not
  answer directly from its head** but use a tool.
- The model **emits special words** that the surrounding program detects; the
  program runs the tool (e.g. a Bing query), and feeds the result text back
  into the model, which then writes the answer.
- Same reason humans use tools: you wouldn't do ratio arithmetic in your
  head; neither is the LLM good at mental math.

## Takeaway

- Capability is no longer just "sampling words in its head" — it is
  **using existing computing infrastructure and tying it together with
  words**. Tool use is a major axis of improvement.
