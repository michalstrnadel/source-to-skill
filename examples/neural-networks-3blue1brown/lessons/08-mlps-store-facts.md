https://www.youtube.com/watch?v=9-Jl0dxWQs8

# Lesson 8 — How might LLMs store facts (Deep Learning Chapter 7)

If a model completes "Michael Jordan plays the sport of ___" with
"basketball", the fact is stored somewhere. Google DeepMind researchers
(studying athlete → sport) found partial results, including that facts seem to
live in the **multi-layer perceptrons (MLPs)**. A full mechanistic account is
still unsolved. Layout inspired by a conversation with Neel Nanda.

## Toy assumptions

- Nearly perpendicular directions in embedding space for **first name
  Michael** (M), **last name Jordan** (J), and **basketball** (B).
- A vector "encodes" a feature when its dot product with that direction is 1
  (0 or negative otherwise).
- "Michael Jordan" spans two tokens, so an earlier attention block must have
  moved "Michael" into the "Jordan" vector.

## The MLP block

Each vector goes through the block **independently and in parallel** (no
cross-talk); the output is **added** to the input vector.

1. **Up-projection `W_up` + bias `b_up`.** Think row by row: each row is a
   direction, and the output entry is its dot product with the vector E (a
   "question" about E). If a row = M + J, the entry is M·E + J·E = 2 for the
   full name, ≤ 1 otherwise; with bias −1 it is positive **only** for
   "Michael Jordan".
   - GPT-3: just under **50,000** rows — exactly **4 × 12,288**, a
     hardware-friendly design choice.
2. **Nonlinearity.** A linear step alone would also fire on "Michael Phelps"
   or "Alexis Jordan". **ReLU** clips negatives to 0 → a clean 1/0, acting like
   an **AND gate**. Models often use **GELU**, a smoother version.
   - These post-nonlinearity values are what people call the transformer's
     **neurons** (active when positive). The classic dots-and-lines neural net
     picture = linear step + element-wise nonlinearity.
3. **Down-projection `W_down` + bias `b_down`.** Think column by column: each
   column is a direction in embedding space, added in proportion to its
   neuron's activation. If column 1 = B, an active "Michael Jordan" neuron adds
   basketball (plus any other associated features). The bias is added every
   time; its purpose is hard to say.
4. Add the result to the input: the vector now encodes Michael, Jordan *and*
   basketball.

Two matrix products, biases, a clipping function between — the same plain
network as the MNIST lessons, but now one piece of a larger architecture. With
GPT-3, it is ~50,000 neurons **times** the number of tokens.

## Finishing the GPT-3 tally

- `W_up` ≈ 604M; `W_down` same (transposed) → ~1.2B per MLP.
- **96** MLPs → ~**116B**, about **2/3** of the total.
- Plus attention, embedding, unembedding → **175B**. Biases and normalization
  parameters are a trivial share.

## Superposition

- The rows/columns-as-directions view is mathematically true, but evidence
  suggests individual neurons rarely represent one clean feature.
- **Superposition hypothesis**: with exactly perpendicular directions an
  n-dimensional space fits only n features (that's the definition of
  dimension). Allow *nearly* perpendicular (89°–91°) and in high dimensions the
  count changes dramatically.
- Demo: 10,000 random 100-dim vectors (100× more vectors than dimensions);
  random angles already cluster near 90°, and after an optimization nudging
  them toward perpendicular, all pairwise angles lie between 89° and 91°.
- **Johnson–Lindenstrauss lemma** consequence: the number of nearly
  perpendicular vectors grows **exponentially** with dimension. A space with
  10× the dimensions can store way more than 10× the independent ideas —
  possibly part of why performance scales well with size.
- Applies to the embedding space *and* the MLP's neuron layer: GPT-3 might
  probe far more than 50,000 features, but then a feature appears as a
  combination of neurons, not one neuron lighting up — making models hard to
  interpret.
- Search term: **sparse autoencoder** — an interpretability tool for
  extracting the true features from superimposed neurons (Anthropic posts
  recommended).

## Not yet covered (promised for later)

Training specifics: the language-model cost function, RLHF fine-tuning,
scaling laws. (Lesson 9 covers the cost function.)
