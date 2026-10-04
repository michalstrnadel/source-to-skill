https://www.youtube.com/watch?v=zjkBMFhNj_g&t=1543s

# 08 — LLM Scaling Laws

- Next-word-prediction accuracy is a **remarkably smooth, well-behaved,
  predictable function of two variables**:
  - **N** — number of parameters;
  - **D** — amount of training text.
- Given N and D, you can predict the achieved accuracy with remarkable
  confidence — and the trends **show no sign of topping out**.
- Consequence: **algorithmic progress is not necessary** — it's a "very nice
  bonus". A bigger computer plus a bigger model trained longer gives a better
  result with high confidence.

## Why next-word accuracy matters

- Nobody cares about next-word accuracy itself, but empirically it
  **correlates with the evaluations we do care about**. Example: going from
  GPT-3.5 to GPT-4 (bigger model, trained longer), accuracy rises across many
  tests.

## Implication

- This is what drives the **compute "gold rush"**: everyone wants a bigger
  GPU cluster and more data, because scaling offers one guaranteed path to
  better models. Organizations still invest heavily in algorithms, but
  scaling is the dependable lever.
