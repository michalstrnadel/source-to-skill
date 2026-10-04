# Methods

## Problem setting (§3)

Sequence transduction with an encoder-decoder: the encoder maps input
symbols (x1..xn) to continuous representations z = (z1..zn); the decoder
generates output symbols (y1..ym) one at a time, auto-regressively, feeding
earlier outputs back in as input.

Motivation (§1, §2): recurrent models compute hidden state h_t from h_(t-1),
so work inside one training example cannot be parallelized, which hurts at
long sequence lengths where memory limits batching. Convolutional
alternatives (Extended Neural GPU, ByteNet, ConvS2S) compute positions in
parallel, but the number of operations linking two distant positions grows
with distance - linearly for ConvS2S, logarithmically for ByteNet. The
Transformer makes this constant, accepting lower effective resolution from
averaging attention-weighted positions, which multi-head attention offsets.

## Encoder and decoder stacks (§3.1)

| Component | Detail |
|---|---|
| Encoder | N = 6 identical layers; sub-layers: multi-head self-attention, position-wise FFN |
| Decoder | N = 6 identical layers; adds a third sub-layer of multi-head attention over the encoder output |
| Sub-layer wrapper | `LayerNorm(x + Sublayer(x))` - residual connection, then layer normalization |
| Width | d_model = 512 for every sub-layer output and the embeddings (so residuals line up) |
| Decoder masking | self-attention cannot see later positions; combined with outputs shifted right by one, prediction i depends only on positions < i |

## Attention (§3.2)

An attention function maps a query and a set of key-value pairs to a
weighted sum of the values; each weight comes from a compatibility function
of the query and its key.

**Scaled dot-product attention (§3.2.1).** Queries and keys of size d_k,
values of size d_v. Dot each query with all keys, divide by √d_k, softmax,
weight the values. In matrix form: `softmax(QKᵀ / √d_k) V`.

- Versus additive attention (a one-hidden-layer feed-forward compatibility
  function): similar theoretical complexity, but dot-product is faster and
  more memory-efficient because it is plain matrix multiplication.
- Why scale: for small d_k the two perform alike, but additive wins over
  unscaled dot-product for large d_k. If q and k have independent
  zero-mean, unit-variance components, q·k has variance d_k; large values
  saturate the softmax and shrink gradients (footnote 4).

**Multi-head attention (§3.2.2).** Project Q, K, V h times with separate
learned matrices W_i^Q, W_i^K (d_model x d_k) and W_i^V (d_model x d_v), run
attention on each in parallel, concatenate, and project with W^O
(h·d_v x d_model). Heads let the model attend to different representation
subspaces at different positions; a single head averages this away.
Setting: h = 8, d_k = d_v = d_model / h = 64, so compute is similar to one
full-dimension head.

**Three uses of attention (§3.2.3).**

1. Encoder-decoder attention: queries from the previous decoder layer,
   keys/values from the encoder output; every decoder position sees the
   whole input.
2. Encoder self-attention: Q, K, V all from the previous encoder layer;
   every position sees every position.
3. Decoder self-attention: each position sees positions up to and including
   itself; leftward flow is blocked by setting illegal softmax inputs to
   -inf.

## Position-wise feed-forward network (§3.3)

`FFN(x) = max(0, xW1 + b1)W2 + b2` - two linear maps with ReLU between,
applied to each position separately with the same weights, but different
weights per layer (equivalently, two kernel-size-1 convolutions). Input and
output 512, inner layer d_ff = 2048.

## Embeddings and softmax (§3.4)

Learned embeddings to d_model for input and output tokens; learned linear
map plus softmax for next-token probabilities. The two embedding layers and
the pre-softmax linear map share one weight matrix. Embedding weights are
multiplied by √d_model.

## Positional encoding (§3.5)

No recurrence or convolution means order must be injected. Positional
encodings of size d_model are summed with the embeddings at the bottom of
both stacks:

- `PE(pos, 2i) = sin(pos / 10000^(2i/d_model))`
- `PE(pos, 2i+1) = cos(pos / 10000^(2i/d_model))`

Each dimension is a sinusoid; wavelengths run geometrically from 2π to
10000·2π. Rationale: for a fixed offset k, PE(pos+k) is a linear function of
PE(pos), which should make relative-position attention easy to learn.
Learned positional embeddings gave nearly identical results; sinusoids were
kept because they may extrapolate to longer sequences than seen in training.

## Why self-attention: the comparison (§4, Table 1)

Three criteria: total compute per layer, parallelizable compute (minimum
sequential operations), and maximum path length between any two positions
(shorter paths make long-range dependencies easier to learn).

| Layer type | Complexity per layer | Sequential ops | Max path length |
|---|---|---|---|
| Self-attention | O(n²·d) | O(1) | O(1) |
| Recurrent | O(n·d²) | O(n) | O(n) |
| Convolutional | O(k·n·d²) | O(1) | O(log_k(n)) |
| Self-attention (restricted to neighborhood r) | O(r·n·d) | O(1) | O(n/r) |

n = sequence length, d = representation size, k = kernel size, r =
neighborhood size.

- Self-attention is cheaper than recurrence when n < d, typical for
  word-piece / byte-pair sentence representations.
- One convolution with k < n does not connect all positions; that takes
  O(n/k) contiguous or O(log_k(n)) dilated layers. Convolutions cost about
  k times a recurrent layer; separable convolutions cut this to
  O(k·n·d + n·d²), which even at k = n equals self-attention plus a
  point-wise FFN - the Transformer's combination.
- Side benefit claimed: attention distributions can be inspected (see
  findings.md, attention visualizations).

## Training (§5)

**Data and batching (§5.1).**

| Task | Data | Vocabulary |
|---|---|---|
| EN-DE | WMT 2014, ~4.5M sentence pairs | byte-pair encoding, shared source-target, ~37000 tokens |
| EN-FR | WMT 2014, 36M sentences | 32000 word-piece vocabulary |

Batches group sentence pairs of similar length, ~25000 source and ~25000
target tokens per batch.

**Hardware and schedule (§5.2).** One machine, 8 NVIDIA P100 GPUs.

| Model | Step time | Steps | Wall clock |
|---|---|---|---|
| Base | ~0.4 s | 100,000 | 12 hours |
| Big | 1.0 s | 300,000 | 3.5 days |

**Optimizer (§5.3).** Adam with β1 = 0.9, β2 = 0.98, ε = 1e-9. Learning rate

`lrate = d_model^-0.5 · min(step_num^-0.5, step_num · warmup_steps^-1.5)`

rises linearly for the first warmup_steps = 4000 steps, then decays with the
inverse square root of the step number.

**Regularization (§5.4).**

- Residual dropout: on each sub-layer output before the residual add and
  normalization, and on the sum of embeddings plus positional encodings in
  both stacks. P_drop = 0.1 for base.
- Label smoothing ε_ls = 0.1: worse perplexity (the model becomes less
  certain) but better accuracy and BLEU.

## Model configurations (Table 3)

| Setting | N | d_model | d_ff | h | d_k | d_v | P_drop | ε_ls | Steps | Params |
|---|---|---|---|---|---|---|---|---|---|---|
| Base | 6 | 512 | 2048 | 8 | 64 | 64 | 0.1 | 0.1 | 100K | 65M |
| Big | 6 | 1024 | 4096 | 16 | 64 | 64 | 0.3 | 0.1 | 300K | 213M |

Table 3 lists only values that differ from base, so the big model's d_k, d_v
and ε_ls are the base values. The EN-FR big model used P_drop = 0.1 instead of 0.3 (§6.1).

## Inference and evaluation (§6.1)

- Checkpoint averaging: base = average of last 5 checkpoints (written every
  10 minutes); big = last 20 checkpoints.
- Beam search, beam size 4, length penalty α = 0.6; tuned on the
  development set.
- Max output length = input length + 50, stopping early when possible.
- Training FLOPs estimated as training time x number of GPUs x sustained
  single-precision throughput per GPU: 2.8, 3.7, 6.0 and 9.5 TFLOPS for K80,
  K40, M40 and P100 (footnote 5).
- Ablations (§6.2) are on EN-DE newstest2013 (dev), with beam search but no
  checkpoint averaging.

## Constituency parsing setup (§6.3)

- 4-layer Transformer, d_model = 1024.
- WSJ portion of the Penn Treebank, ~40K training sentences, 16K vocab.
- Semi-supervised: plus high-confidence and BerkeleyParser corpora,
  ~17M sentences, 32K vocab.
- Only dropout (attention and residual), learning rate and beam size tuned
  on Section 22 dev; everything else as the EN-DE base model.
- Inference: max output length = input length + 300, beam size 21,
  α = 0.3.

## Code

Training and evaluation code: https://github.com/tensorflow/tensor2tensor
(§7).
