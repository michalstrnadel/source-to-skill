https://www.youtube.com/watch?v=zjkBMFhNj_g&t=1265s

# 07 — Appendix: comparisons, labeling docs, RLHF, synthetic data, leaderboard

## Stage 3 (optional): comparison labels

- **Comparing is easier than generating.** Writing a haiku about paperclips
  may be hard for a labeler; picking the best of several candidate haikus
  produced by the stage-2 assistant is easy.
- Stage 3 fine-tunes further using these comparisons. At OpenAI this is
  called **reinforcement learning from human feedback (RLHF)**. It is optional
  and buys additional performance.

## Labeling instructions

- Excerpt shown from OpenAI's InstructGPT paper: labelers are asked to make
  responses **helpful, truthful and harmless**.
- Real labeling documentation can run to **tens or hundreds of pages**.

## Labeling is increasingly human–machine collaboration

- "Humans do all the manual work" is increasingly inaccurate. Options:
  - models sample answers, people cherry-pick parts into one best answer;
  - models check the labeler's work;
  - models create comparisons, humans only oversee.
- Think of it as a **slider** of human vs model involvement; as models
  improve, the slider moves toward the model side.

## Leaderboard: Chatbot Arena

- Run by a team at Berkeley; ranks models by **Elo**, computed like in chess.
  Users ask a question, see responses from two anonymous models, pick the
  winner.
- Snapshot at the time: **proprietary models on top** (OpenAI's GPT series,
  Anthropic's Claude series, a few others) — closed weights, used via web
  interfaces. **Open-weights models below** (Meta's Llama 2 series; Zephyr 7B
  beta, based on Mistral from a French startup).
- Dynamic: closed models work better but you can't download or fine-tune
  them; open models are worse but may be good enough for your application,
  and the open ecosystem is chasing the proprietary one.
