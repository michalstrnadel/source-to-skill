---
name: how-transformers-work
description: How the Transformer and its attention mechanism work, synthesized from the original paper (Vaswani et al., "Attention Is All You Need"), 3Blue1Brown's "Attention in transformers, step-by-step" video, and Jay Alammar's "The Illustrated Transformer". Load when explaining or implementing self-attention, Q/K/V, multi-head attention, masking, positional encoding, encoder-decoder vs decoder-only, transformer dimensions and parameter counts, or when reconciling the different notations and intuitions these three classic explanations use.
---

# How transformers work

Three canonical explanations of one architecture: the paper that defined it
[S1], a visual walkthrough of attention in a GPT-style model [S2], and an
illustrated tour of the full encoder-decoder [S3]. They agree on the math;
they differ in framing, notation, example dimensions and what they call the
key insight — see [disagreements.md](disagreements.md) before quoting one
source's convention as "the" convention.

## Core ideas

1. **Attention is a learned, content-based weighted sum.** Each position
   emits a query; every position emits a key and a value; query-key dot
   products, scaled by 1/sqrt(d_k) and softmaxed, weight the sum of values.
   Formula: `Attention(Q,K,V) = softmax(QK^T / sqrt(d_k)) V`. [S1][S2][S3]
2. **Attention exists to put context into token vectors.** A token's initial
   embedding is a context-free lookup ("mole" is the same vector in every
   sentence); attention blocks move information between positions so the
   vector comes to mean the word *in this context* ("it" absorbs "animal";
   "creature" absorbs "fluffy blue"). [S2][S3]
3. **Q, K and V are three separate learned projections.** In the paper's
   base model each projects 512-d embeddings down to 64 dims per head.
   Q and K must share a dimension (they are dot-producted); V may differ
   (d_v). [S1][S3] In GPT-3 numbers: 12,288-d embeddings, 128-d key/query
   space. [S2]
4. **Scaling by sqrt(d_k) keeps softmax trainable.** With unit-variance
   components, a q·k dot product has variance d_k; large scores push softmax
   into regions with vanishing gradients. [S1] (S2 and S3 give only the
   short "stability" rationale.)
5. **Masking = set illegal scores to −∞ before softmax**, so they become
   exactly 0 and rows/columns still sum to 1. Used in decoder self-attention
   so a position never sees later tokens. [S1][S2][S3]
6. **Multi-head attention runs h attention functions in parallel** with
   separate projections, then combines them (concatenate + W^O). Each head
   can learn a different relation (coreference, adjective→noun, syntax);
   a single head averages them away. Per-head dims shrink (d_model/h) so
   total cost stays about the same as one full-width head. [S1][S2][S3]
7. **No recurrence means order must be injected.** Positional encodings
   (sinusoids in the paper) are added to embeddings at the bottom of the
   stack. [S1][S3] (S2 treats position as already present in the embedding.)
8. **A layer = attention sub-layer + position-wise feed-forward sub-layer**,
   each wrapped in a residual connection and layer norm:
   `LayerNorm(x + Sublayer(x))`. The FFN is applied to each position
   independently (512 → 2048 → 512 in the base model). [S1][S3]
   Most parameters live outside attention: in GPT-3, attention is ~58B of
   175B. [S2]
9. **Three uses of attention.** Encoder self-attention (all-to-all),
   masked decoder self-attention (causal), and encoder-decoder /
   cross-attention (queries from the decoder, keys and values from the
   encoder output; no mask). [S1][S2][S3]
10. **The real win is parallelism.** Self-attention connects any two
    positions in O(1) sequential steps (RNNs need O(n)), so training
    parallelizes on GPUs; the base model trained in 12 hours on 8 P100s.
    [S1] All three sources call this the decisive advantage. [S1][S2][S3]
11. **Cost is quadratic in context.** The attention pattern is n×n;
    complexity per layer O(n²·d). This is why context length is a
    bottleneck. [S1][S2]

## Key numbers (paper base model unless noted)

- N = 6 encoder + 6 decoder layers; d_model = 512; d_ff = 2048; h = 8;
  d_k = d_v = 64; dropout 0.1; label smoothing 0.1; 65M params. [S1]
- Big model: d_model 1024, d_ff 4096, h = 16, dropout 0.3, 213M params,
  28.4 BLEU EN-DE. [S1]
- GPT-3 (as counted in S2): 96 layers × 96 heads; ~6.3M params per head
  (4 matrices of 12,288 × 128); ~600M per attention block; ~58B total for
  attention. [S2]

## Sources

| id | title | type | one-line takeaway | file |
|----|-------|------|-------------------|------|
| S1 | Attention Is All You Need (Vaswani et al., NIPS 2017) | paper | Attention alone, without recurrence or convolution, gives better translation at a fraction of the training cost. | [sources/01-attention-is-all-you-need.md](sources/01-attention-is-all-you-need.md) |
| S2 | Attention in transformers, step-by-step (3Blue1Brown, 2024) | video | Attention heads compute context-dependent *updates* (Δe) added to embeddings; queries ask, keys answer, values say what to add. | [sources/02-3b1b-attention-step-by-step.md](sources/02-3b1b-attention-step-by-step.md) |
| S3 | The Illustrated Transformer (Jay Alammar, 2018) | article | The full encoder-decoder, walked through vector by vector with the paper's dimensions, from embedding to beam search. | [sources/03-illustrated-transformer.md](sources/03-illustrated-transformer.md) |

## Files

- [disagreements.md](disagreements.md) — where the sources differ in
  notation, definitions, numbers, and claimed key insight (read before
  mixing conventions).
- [cheatsheet.md](cheatsheet.md) — step-by-step recipes (compute one
  attention head, count parameters, build a layer), each tagged by source.
- `sources/NN-*.source.json` — extraction manifests for refreshing.

## Which source to reach for

- Exact definitions, hyperparameters, ablations, results: S1.
- Intuition for *what* Q/K/V do and parameter counting at GPT scale: S2.
- Encoder-decoder data flow, decoder loop, output layer, loss, beam
  search: S3.
