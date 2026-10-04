https://www.youtube.com/watch?v=eMlx5fFNoYc

# Lesson 7 — Attention in transformers, step-by-step (Deep Learning Chapter 6)

Attention debuted in the 2017 paper *Attention Is All You Need*. Many find it
confusing; give it time.

## What attention is for

- Initial token embeddings are a context-free lookup: "mole" gets the same
  vector in "American shrew mole", "one mole of carbon dioxide" and "biopsy of
  the mole". Attention computes what to **add** to the generic embedding to
  move it toward the context-specific meaning.
- "tower" → preceded by "Eiffel" → move toward Paris/France/steel; add
  "miniature" → no longer correlated with large, tall things.
- More generally, attention moves information from one embedding to another,
  possibly far away and richer than a single word. In "...therefore the
  murderer was", the final vector must absorb everything relevant from the
  whole context window.

## One attention head (toy goal: adjectives update nouns)

Example: "a fluffy blue creature roamed the verdant forest". Embeddings `e`
encode both the word and its position. The adjective→noun behavior is an
illustrative invention; real heads are much harder to interpret.

1. **Queries.** `W_Q · e` gives each token a query (e.g. 128-dim, much smaller
   than the embedding) — imagine the noun asking "any adjectives in front of
   me?"
2. **Keys.** `W_K · e` gives each token a key in the same small space — answers
   to queries; a key matches a query when they align.
3. **Scores.** Dot product of every key with every query → a grid. Large where
   "fluffy"/"blue" keys align with the "creature" query ("fluffy and blue
   attend to creature"); small or negative for unrelated pairs.
4. **Normalize.** Softmax each column so it sums to 1 → the **attention
   pattern**. For numerical stability divide scores by √(key-query
   dimension) first. Paper notation: softmax(QKᵀ/√d_k)·V.
5. **Masking.** Training predicts the next token after *every* prefix
   simultaneously (one example acts as many), so later tokens must not
   influence earlier ones. Set those entries to −∞ **before** softmax → they
   become 0 and columns stay normalized. GPT always applies masking.
6. **Values.** `W_V · e` gives each token a value vector in the full embedding
   space — "if this word is relevant to something else, what should be added
   to its embedding?" For each column, weight the values by the attention
   pattern and sum → Δe; add Δe to the original embedding. Applied to every
   column → a sequence of refined embeddings.

## Cost and parameters (GPT-3)

- The attention pattern has size **context²** — why context length is a hard
  bottleneck; recent variants aim to make it more scalable.
- `W_Q`, `W_K`: 128 × 12,288 each → ~1.5M parameters apiece.
- A full 12,288 × 12,288 value map would be ~150M parameters. In practice it is
  **factored (low rank)**: "value down" (12,288 → 128) times "value up"
  (128 → 12,288), so value parameters equal key + query. (These names are the
  course's own, not conventional.)
- Four equal-size matrices → **~6.3M parameters per head**.

### Convention warning

In papers and code, all heads' "value up" matrices are stapled together into
one **output matrix** for the whole multi-head block; "the value matrix" of a
head usually means only the value-down projection.

## Self- vs cross-attention

Self-attention (above) uses one sequence. **Cross-attention** has keys and
queries from different data (e.g. two languages in translation, audio and
transcript); typically no masking.

## Multi-head attention

- Many ways context changes meaning ("they crashed the car" → shape of the
  car; "wizard" near "Harry" → Harry Potter; "Queen, Sussex, William" → the
  prince). Each needs different key/query/value maps.
- GPT-3 runs **96 heads** per block; each proposes a change for every
  position; changes are summed and added to the embedding.
- ~600M parameters per multi-head block; **96 layers** → just under **58B**
  for attention — only about **1/3** of 175B. Most parameters live in the MLP
  blocks between attention steps.
- Repeated blocks let already-nuanced embeddings absorb more nuanced context,
  potentially encoding abstractions like sentiment, tone, "is this a poem",
  relevant scientific facts.

## Why attention won

Less any specific behavior than that it is **extremely parallelizable** on
GPUs — and a big lesson of the last decade or two is that scale alone gives
large qualitative improvements.

Further resources recommended: anything by Andrej Karpathy or Chris Olah;
Vivek's videos on the motivation; Art of the Problem's history of LLMs.
