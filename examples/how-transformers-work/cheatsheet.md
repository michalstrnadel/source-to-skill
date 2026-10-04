# Cheatsheet

Tags: [S1] paper, [S2] 3Blue1Brown video, [S3] Illustrated Transformer.

## Compute one self-attention head

1. Stack the n input vectors as rows of X (n × d_model). [S3]
2. Project: Q = XW^Q, K = XW^K (n × d_k), V = XW^V (n × d_v). [S1][S3]
3. Score: S = QK^T (n × n), one row per query. [S1][S3]
4. Scale: S / sqrt(d_k); d_k = 64 → divide by 8. [S1][S3]
5. Mask (causal/decoder only): set S[i, j] = −∞ for j > i. Use −∞, not 0,
   so that the normalized weights still sum to 1. [S1][S2][S3]
6. Softmax over the key axis (each row sums to 1). If you are following
   S2's grid, which is transposed, softmax runs down columns there. [S1][S2]
7. Output Z = softmax(...) · V; the output for row i is the weighted sum of
   the value vectors. [S1][S2][S3]

## Multi-head attention

- Run h heads with separate W^Q, W^K, W^V; set d_k = d_v = d_model / h so
  the total cost matches one full-width head. [S1][S3]
- Concatenate the head outputs (n × h·d_v) and multiply by W^O (h·d_v ×
  d_model). [S1][S3] This is the same as summing per-head updates, where
  each head's update is its output times its own slice of W^O. [S2]
- Choosing h: in S1's ablation, 1 head scored 0.9 BLEU below the best and
  32 heads also scored lower. 8–16 heads worked best at d_model = 512.
  [S1]

## Build a layer

- Encoder layer: `x = LayerNorm(x + MHA(x))`, then
  `x = LayerNorm(x + FFN(x))`. [S1][S3]
- FFN: `max(0, xW1 + b1)W2 + b2`, applied per position (512 → 2048 → 512).
  [S1]
- Decoder layer: masked self-attention → encoder-decoder attention (Q from
  the decoder, K/V from the final encoder output) → FFN, each with a
  residual connection and LayerNorm. [S1][S3]
- Dropout 0.1 on each sub-layer output before the residual add, and on the
  embedding + positional-encoding sum. [S1]

## Inputs and outputs

- Embed tokens, multiply by sqrt(d_model), and add positional encodings
  (sin on even dims, cos on odd dims: `pos / 10000^(2i/d_model)`). [S1]
- Tie the input embedding, output embedding and pre-softmax weights. [S1]
- Output head: a linear layer to vocabulary-size logits, then softmax.
  [S1][S3]
- Decode greedily (argmax) or with beam search. S1 used beam 4 and length
  penalty 0.6, with max length = input + 50. [S1][S3]

## Train (S1 recipe)

- Adam (β1 0.9, β2 0.98, ε 1e-9). LR = d_model^−0.5 · min(step^−0.5,
  step · 4000^−1.5): linear warm-up for 4000 steps, then inverse-square-root
  decay. [S1]
- Label smoothing 0.1: perplexity gets worse, BLEU improves. [S1]
- Batch about 25k source + 25k target tokens, grouped by length. [S1]
- Average the last 5–20 checkpoints for inference. [S1]
- Train on every prefix in parallel (with a causal mask). One
  sequence then gives n training targets. [S2]

## Count parameters (S2 method)

- Per head: W_Q and W_K are each d_head × d_model, and the value-down and
  value-up matrices have the same size. That is 4 · d_model · d_head in
  total. GPT-3: 4 × 12,288 × 128 ≈ 6.3M. [S2]
- Per attention block: × heads (96) ≈ 600M. Whole model: × layers (96) ≈
  58B, about a third of 175B. [S2]

## Decision rules

- Writing code or citing a hyperparameter: use S1's names and values (W^O,
  d_v = 64, fixed sinusoidal PE). [S1]
- Explaining intuition: start from "embeddings are context-free lookups;
  attention computes the context update Δe". [S2]
- Explaining data flow end to end (decoder loop, logits, loss): use S3's
  walkthrough. [S3]
- Long contexts: attention memory and compute grow as n². Consider
  restricted/local attention (S1 §4 proposes a neighborhood r, which gives
  path length O(n/r)). [S1][S2]
- "Which head does what?": treat any story (adjective → noun, coreference)
  as illustrative. Real heads are learned and hard to interpret. [S2]
  S1's Figures 3–5 show a few heads that can be interpreted. [S1]

## Anti-patterns

- Setting masked scores to 0 instead of −∞ breaks normalization. [S2]
- Dropping the sqrt(d_k) scale saturates softmax at large d_k, and
  dot-product attention then underperforms additive attention. [S1]
- Mixing S2's column convention with row-major `QK^T` code softmaxes over
  the wrong axis. [S1][S2]
- Assuming attention holds most of the parameters: in GPT-3 it is about
  one third. [S2]
- Treating positional encodings as necessarily learned: the original model
  uses fixed sinusoids, and learned ones tie. [S1] (S3 states the opposite;
  see disagreements.md #1.)
