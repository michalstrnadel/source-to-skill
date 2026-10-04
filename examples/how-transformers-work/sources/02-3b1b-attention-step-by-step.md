https://www.youtube.com/watch?v=eMlx5fFNoYc

# S2 — Attention in transformers, step-by-step (3Blue1Brown, Deep Learning Chapter 6)

Grant Sanderson, 3Blue1Brown, uploaded 2024-04-07, 26 min. Runs on a
GPT-style next-token predictor, using GPT-3's numbers for scorekeeping.
Simplifies tokens to whole words.

## Core ideas

- An attention block's job is to compute a context-dependent **change** to
  each embedding — an update Δe added to the original vector — so a
  generic word direction moves toward its in-context meaning.
- Query = a question a token asks ("any adjectives in front of me?"),
  key = a potential answer, their dot product = how well they match,
  value = *what should be added* to the asking token if the match is good.
- Everything learned is a matrix of tunable weights; the adjective→noun
  story is an invented illustration, real heads are much harder to read.
- Prediction of the next token depends only on the **last** vector of the
  sequence, so attention must route everything relevant into it.
- Parallelizability, not any specific behavior, is a big part of why
  attention won.

## Segments

### Recap on embeddings — https://www.youtube.com/watch?v=eMlx5fFNoYc&t=0s
- Model goal: predict the next token. First step: map each token to a
  high-dimensional embedding.
- Directions in embedding space carry meaning (e.g. a gender direction).
- A transformer progressively adjusts embeddings to encode rich contextual
  meaning, not just the single word.

### Motivating examples — https://www.youtube.com/watch?v=eMlx5fFNoYc&t=99s
- "American shrew mole" / "one mole of carbon dioxide" / "biopsy of the
  mole": the initial embedding of "mole" is identical in all three (a
  context-free lookup). Only attention lets neighbors push it toward the
  right meaning.
- "tower" → "Eiffel tower" (Paris, steel) → "miniature Eiffel tower" (no
  longer large/tall): successive refinement.
- Attention can move information across long distances and carry more than
  single-word meaning. Mystery-novel example: the final "was" vector must
  absorb everything needed to predict the murderer.

### The attention pattern — https://www.youtube.com/watch?v=eMlx5fFNoYc&t=269s
- Running example: "a fluffy blue creature roamed the verdant forest";
  one head, adjectives updating nouns.
- Embeddings (e) encode both the word and its position.
- Query q = W_Q·e, in a smaller space (128 dims). Key k = W_K·e, same
  smaller space. Keys "answer" queries when aligned.
- Grid of all key-query dot products; large where fluffy/blue keys align
  with the creature query. Softmax **down each column** (one column per
  query) so each column sums to 1. The normalized grid = the attention
  pattern.
- Ties it to the paper's `softmax(QK^T / sqrt(d_k)) V`; the sqrt(d_k)
  division is "for numerical stability".

### Masking — https://www.youtube.com/watch?v=eMlx5fFNoYc&t=668s
- Training predicts the next token after **every** prefix simultaneously,
  so one passage acts as many training examples.
- Therefore later tokens must not influence earlier ones (they would give
  away the answer). Setting those entries to 0 would break normalization;
  set them to −∞ before softmax instead.
- In the GPT example masking is always applied, even at inference.

### Context size — https://www.youtube.com/watch?v=eMlx5fFNoYc&t=762s
- The pattern's size is the square of the context size → context length is
  a major bottleneck; newer variants aim to make it scale.

### Values — https://www.youtube.com/watch?v=eMlx5fFNoYc&t=790s
- Value matrix W_V maps an embedding (e.g. fluffy) to a value vector that
  lives in the **full embedding space** (~12,000 dims) and is added to the
  target (creature).
- For each column: weight every value vector by the pattern, sum → Δe; add
  Δe to the original embedding. Done for every column → a sequence of
  refined embeddings.

### Counting parameters — https://www.youtube.com/watch?v=eMlx5fFNoYc&t=944s
- W_Q, W_K: 128 × 12,288 each ≈ 1.5M params.
- A full square W_V would be 12,288 × 12,288 ≈ 150M — possible, but in
  practice the value map is **factored** into "value down" (to 128 dims)
  and "value up" (back to 12,288) — a low-rank map (Sanderson's own,
  non-standard names).
- Four equal-size matrices → ~6.3M params per head.

### Cross-attention — https://www.youtube.com/watch?v=eMlx5fFNoYc&t=1101s
- Same as self-attention but keys and queries come from different data
  (source vs target language; audio vs transcript). Typically no masking.

### Multiple heads — https://www.youtube.com/watch?v=eMlx5fFNoYc&t=1159s
- Many kinds of contextual update ("they crashed the car"; "Harry" near
  "wizard" vs near "Queen, Sussex, William") → many heads, each with its
  own K, Q, V maps.
- GPT-3: 96 heads per block. Each head proposes a Δe per position; the
  proposals are **summed** and added to the embedding.
- ~600M params per multi-head attention block.

### The output matrix — https://www.youtube.com/watch?v=eMlx5fFNoYc&t=1336s
- In papers and implementations, all heads' "value up" matrices are stapled
  into one **output matrix** for the whole block; a head's "value matrix"
  usually means only the value-down projection. Same computation,
  different bookkeeping.

### Going deeper — https://www.youtube.com/watch?v=eMlx5fFNoYc&t=1399s
- Data alternates between attention and MLP blocks, many times; deeper
  layers can encode more abstract features (sentiment, tone, genre).
- GPT-3: 96 layers → just under 58B attention params, about a third of
  175B. Most parameters sit in the blocks between attention steps.

### Ending — https://www.youtube.com/watch?v=eMlx5fFNoYc&t=1494s
- Attention's success owes much to being extremely parallelizable on GPUs,
  given that scale alone has produced big quality gains.

## Highlights

- "this initial token embedding is effectively a lookup table with no
  reference to the context" (segment from
  [1:39](https://www.youtube.com/watch?v=eMlx5fFNoYc&t=99s))
- "So even though attention gets all of the attention, the majority of
  parameters come from the blocks sitting in between these steps."
  (segment from [23:19](https://www.youtube.com/watch?v=eMlx5fFNoYc&t=1399s))
