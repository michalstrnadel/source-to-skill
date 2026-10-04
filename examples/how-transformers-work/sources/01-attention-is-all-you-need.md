https://arxiv.org/abs/1706.03762

# S1 — Attention Is All You Need

Vaswani, Shazeer, Parmar, Uszkoreit, Jones, Gomez, Kaiser, Polosukhin
(Google Brain / Google Research / U. Toronto). NIPS 2017; extracted text is
arXiv v7 (2 Aug 2023). Code: tensor2tensor.

## TL;DR

The Transformer is an encoder-decoder built only from attention and
position-wise feed-forward layers, with no recurrence or convolution. It
beats prior translation systems (including ensembles) on WMT 2014 EN-DE
and EN-FR while training far faster, and transfers to constituency parsing.

## Key claims and evidence

- **Recurrence is the bottleneck.** RNNs compute h_t from h_(t−1), which
  blocks parallelism within a training example (§1). Self-attention needs
  O(1) sequential operations and O(1) maximum path length between any two
  positions vs O(n) for recurrent layers (§4, Table 1).
- **Self-attention is cheaper than recurrence when n < d**, which holds for
  typical word-piece / BPE sentence lengths (§4). Per-layer cost: self-
  attention O(n²·d), recurrent O(n·d²), convolutional O(k·n·d²),
  restricted self-attention O(r·n·d) with path length O(n/r) (Table 1).
- **SOTA translation at low cost.** Big model: 28.4 BLEU EN-DE (over 2 BLEU
  above best prior incl. ensembles) at 2.3·10^19 training FLOPs; base model
  27.3 BLEU at 3.3·10^18 FLOPs, already beating all prior models and
  ensembles (§6.1, Table 2).
- **Multi-head matters, but not monotonically.** One head is 0.9 BLEU worse
  than the best setting; quality also drops with too many heads (§6.2,
  Table 3 A).
- **Generalizes beyond translation.** A 4-layer Transformer reaches 91.3 F1
  (WSJ only) and 92.7 F1 (semi-supervised) on WSJ §23 parsing, beating all
  prior models except the RNN Grammar (§6.3, Table 4).
- **Attention heads look interpretable.** In encoder layer 5 of 6, heads
  follow the long-distance dependency "making … more difficult" and appear
  to resolve anaphora ("its" → "Law") (§4, Figures 3–5).

## Architecture (§3)

- **Stacks:** encoder and decoder each N = 6 identical layers. Encoder layer
  = multi-head self-attention + FFN. Decoder adds a third sub-layer:
  multi-head attention over encoder output. Each sub-layer is wrapped as
  `LayerNorm(x + Sublayer(x))`; all outputs are d_model = 512 (§3.1).
- **Decoder masking:** self-attention is masked so position i only sees
  positions < i; combined with output embeddings shifted right by one, this
  keeps generation auto-regressive (§3.1). Implemented by setting illegal
  softmax inputs to −∞ (§3.2.3).
- **Attention definition:** a function mapping a query and a set of
  key-value pairs to an output; the output is a weighted sum of values,
  weights from a compatibility function of query and key (§3.2).
- **Scaled dot-product attention (§3.2.1):**
  `softmax(QK^T / sqrt(d_k)) V`. Chosen over additive attention because it
  runs as optimized matrix multiplication. Scaling reason: if q and k
  components are independent with mean 0 and variance 1, q·k has variance
  d_k; large dot products push softmax into tiny-gradient regions, and
  unscaled dot-product attention loses to additive attention at large d_k.
- **Multi-head (§3.2.2):** `MultiHead = Concat(head_1..head_h) W^O`,
  `head_i = Attention(Q W_i^Q, K W_i^K, V W_i^V)`; W^Q, W^K ∈ R^(d_model×d_k),
  W^V ∈ R^(d_model×d_v), W^O ∈ R^(h·d_v×d_model). h = 8, d_k = d_v = 64.
  Rationale: lets the model attend to different representation subspaces at
  different positions; one head's averaging inhibits this. Total cost ≈ one
  full-width head.
- **Three uses (§3.2.3):** encoder-decoder attention (Q from decoder, K/V
  from encoder output), encoder self-attention, masked decoder
  self-attention.
- **FFN (§3.3):** `max(0, xW1 + b1)W2 + b2`, 512 → 2048 → 512, same across
  positions, different per layer ("two convolutions with kernel size 1").
- **Embeddings (§3.4):** input embedding, output embedding and pre-softmax
  linear share one weight matrix; embedding weights multiplied by
  sqrt(d_model).
- **Positional encoding (§3.5):** fixed sinusoids added to embeddings:
  `PE(pos,2i) = sin(pos/10000^(2i/d_model))`,
  `PE(pos,2i+1) = cos(pos/10000^(2i/d_model))`; wavelengths 2π…10000·2π.
  Chosen because PE(pos+k) is a linear function of PE(pos) (hypothesized to
  ease relative attention) and may extrapolate to longer sequences. Learned
  positional embeddings gave nearly identical results (Table 3 E).

## Methods / training (§5)

- Data: WMT14 EN-DE ~4.5M sentence pairs, shared BPE vocab ~37,000;
  WMT14 EN-FR 36M sentences, 32,000 word-piece vocab. Batches ≈ 25,000
  source + 25,000 target tokens, grouped by length.
- Hardware: one machine, 8 × P100. Base: 0.4 s/step, 100K steps, 12 hours.
  Big: 1.0 s/step, 300K steps, 3.5 days.
- Optimizer: Adam β1 = 0.9, β2 = 0.98, ε = 10^−9;
  `lrate = d_model^−0.5 · min(step^−0.5, step · warmup^−1.5)`, warmup 4000
  (linear warm-up, then inverse-sqrt decay).
- Regularization: residual dropout 0.1 on each sub-layer output and on
  embedding + PE sums; label smoothing ε_ls = 0.1 (hurts perplexity, helps
  BLEU).
- Inference: average last 5 (base) / 20 (big) checkpoints; beam size 4,
  length penalty α = 0.6; max output length = input + 50.

## Findings (Table 3, EN-DE dev newstest2013)

- Base: 4.92 PPL, 25.8 BLEU, 65M params. Big: 4.33 PPL, 26.4 BLEU, 213M.
- (A) heads/dims at constant compute: h=1 (d_k=512) 24.9; h=4 25.5;
  h=16 25.8; h=32 (d_k=16) 25.4.
- (B) smaller d_k hurts (d_k=16: 25.1; 32: 25.4) — suggests compatibility is
  hard and a richer function than dot product could help.
- (C) bigger is better: d_model 1024 → 26.0; d_ff 4096 → 26.2; N=2 → 23.7.
- (D) dropout 0.0 → 24.6 (overfitting); label smoothing 0.0 → 25.3.
- (E) learned positional embeddings: 25.7 (vs 25.8).

## Limitations and caveats

- Quadratic per-layer cost in n; the paper proposes restricted
  (neighborhood r) self-attention for long inputs and leaves it to future
  work (§4, §7).
- Attention averaging reduces effective resolution; multi-head is the
  stated counter-measure (§2).
- Generation remains sequential at inference; "less sequential generation"
  is listed as a goal (§7).
- Text inconsistency: abstract says EN-FR 41.8 BLEU; §6.1 says 41.0 (Table 2
  lists 41.8). See [disagreements.md](../disagreements.md).
- Evaluation is translation + one parsing task; non-text modalities are
  future work (§7).

## Glossary

- **Auto-regressive:** each output step consumes previously generated
  symbols.
- **d_k / d_v / d_model / d_ff:** key/query dim, value dim, residual-stream
  width, FFN inner width.
- **Encoder-decoder attention:** queries from decoder, keys/values from
  encoder output.
- **Label smoothing:** soft targets (ε_ls = 0.1) instead of one-hot.
- **Maximum path length:** longest chain of operations between any two
  positions; shorter makes long-range dependencies easier to learn.
- **Multi-head attention:** h parallel attention functions on different
  learned projections, concatenated and projected by W^O.
- **Scaled dot-product attention:** softmax(QK^T/sqrt(d_k))V.
- **Self-attention (intra-attention):** attention relating positions within
  one sequence.

## Citation

Vaswani, A., Shazeer, N., Parmar, N., Uszkoreit, J., Jones, L., Gomez,
A. N., Kaiser, Ł., Polosukhin, I. (2017). Attention Is All You Need.
NIPS 2017. arXiv:1706.03762. The reference list (40 entries) is in the
original; key ones: layer norm [1], Bahdanau attention [2], residual
connections [11], LSTM [13], Adam [20], dropout [33], label smoothing [36].
