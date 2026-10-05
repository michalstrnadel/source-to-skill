https://www.youtube.com/watch?v=zjkBMFhNj_g&t=2282s

# 12 — Self-improvement: the LLM AlphaGo question

## AlphaGo's two stages (DeepMind)

1. **Imitation:** learn from games played by human experts (filtered to the
   best players). Works, but can only be as good as the best human. [38:02](https://www.youtube.com/watch?v=zjkBMFhNj_g&t=2282s)
2. **Self-improvement:** Go is a closed sandbox with a simple, cheap,
   automatic reward function — did you win? [38:02](https://www.youtube.com/watch?v=zjkBMFhNj_g&t=2282s) Play millions of games, optimize
   for win probability, no imitation required. AlphaGo surpassed some of the
   best human players in **40 days**. [39:02](https://www.youtube.com/watch?v=zjkBMFhNj_g&t=2342s)

## LLMs are stuck at step 1

- Today LLMs imitate human labelers' answers. Even with excellent labelers,
  it's hard to exceed human response quality by training only on humans. [39:02](https://www.youtube.com/watch?v=zjkBMFhNj_g&t=2342s)
- **The obstacle:** language is open-ended with many task types — there is
  **no simple, fast, general reward criterion** telling you whether a sample
  was good or bad. [40:04](https://www.youtube.com/watch?v=zjkBMFhNj_g&t=2404s)
- **Outlook:** in **narrow domains** a reward function may be achievable, so
  self-improvement there is plausible. [40:04](https://www.youtube.com/watch?v=zjkBMFhNj_g&t=2404s) Self-improvement in the general case is
  an open question.
