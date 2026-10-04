---
name: attention-is-all-you-need
description: The Transformer paper (Vaswani et al., NIPS 2017, arXiv 1706.03762) distilled - scaled dot-product and multi-head attention, encoder-decoder stacks, sinusoidal positional encoding, the warmup learning-rate schedule, base/big hyperparameters, WMT 2014 translation and constituency-parsing results, and the ablation table. Load when explaining, implementing, or checking details of the original Transformer, comparing self-attention against recurrent or convolutional layers, or citing the paper's numbers.
---

# Attention Is All You Need (Vaswani et al., 2017)

Source: https://arxiv.org/abs/1706.03762 (NIPS 2017; extracted from arXiv v7)

## TL;DR

The Transformer is an encoder-decoder model for sequence transduction built
only from attention and position-wise feed-forward layers, with no
recurrence and no convolution. Because every position attends to every
other position in one step, training parallelizes well and any two positions
are a constant number of operations apart. It set new state-of-the-art BLEU
on WMT 2014 EN-DE (28.4) and EN-FR (single model) at a fraction of earlier
training costs, and transferred to English constituency parsing.

## Key claims and evidence

1. **Attention alone is enough for strong sequence transduction.**
   Transformer (big) reaches 28.4 BLEU on WMT 2014 EN-DE, more than 2.0 BLEU
   above the best earlier results including ensembles; even the base model
   (27.3) beats all earlier models and ensembles. (§6.1, Table 2)
2. **It is much cheaper to train.** Base: 12 hours / 100K steps on 8 P100
   GPUs, ~3.3e18 FLOPs. Big: 3.5 days / 300K steps, ~2.3e19 FLOPs. The EN-FR
   big model beats all earlier single models at under 1/4 the training cost
   of the previous state of the art. (§5.2, §6.1, Table 2)
3. **Self-attention beats recurrence on parallelism and path length.** A
   self-attention layer needs O(1) sequential operations and has O(1)
   maximum path length versus O(n) for both in a recurrent layer; per-layer
   cost O(n²·d) is lower than recurrent O(n·d²) whenever sequence length n
   is below representation size d, the usual case for subword-tokenized
   sentences. (§4, Table 1)
4. **Scaling the dot product by 1/√d_k matters.** With large d_k the dot
   products grow (variance d_k for unit-variance components) and push the
   softmax into tiny-gradient regions; unscaled dot-product attention is
   beaten by additive attention at large d_k. (§3.2.1, footnote 4)
5. **Multiple heads help, but not without limit.** Single-head attention is
   0.9 BLEU worse than the best setting; 32 heads also degrade quality.
   Shrinking d_k hurts, suggesting compatibility is hard to compute. (§6.2,
   Table 3 rows A-B)
6. **Sinusoidal and learned positional encodings perform about the same**
   (25.7 vs 25.8 dev BLEU); sinusoids were kept for possible extrapolation
   to longer sequences. (§3.5, Table 3 row E)
7. **It generalizes beyond translation.** A 4-layer Transformer reaches 91.3
   F1 (WSJ only) and 92.7 F1 (semi-supervised) on WSJ section 23, beating
   every earlier model except the Recurrent Neural Network Grammar, with
   little task-specific tuning. (§6.3, Table 4)

## The architecture in one screen

- **Stacks:** encoder and decoder each have N = 6 identical layers. Every
  sub-layer is wrapped as `LayerNorm(x + Sublayer(x))` (residual + layer
  norm, post-norm). All sub-layers and embeddings output d_model = 512.
- **Encoder layer:** multi-head self-attention, then position-wise FFN.
- **Decoder layer:** masked multi-head self-attention, then encoder-decoder
  attention (queries from decoder, keys/values from encoder output), then
  FFN. Masking (illegal connections set to -inf before softmax) plus the
  one-position shift of output embeddings keeps prediction i dependent only
  on outputs before i.
- **Attention:** `Attention(Q,K,V) = softmax(QKᵀ / √d_k) V`.
- **Multi-head:** h = 8 heads, each projecting Q, K, V to d_k = d_v = 64,
  outputs concatenated and projected by W^O. Total cost is close to one
  full-width head.
- **FFN:** `max(0, xW1 + b1)W2 + b2`, inner size d_ff = 2048, same at every
  position but different per layer.
- **Embeddings:** one weight matrix shared by input embedding, output
  embedding and pre-softmax projection; embeddings scaled by √d_model.
- **Positional encoding:** added to embeddings;
  `PE(pos,2i) = sin(pos / 10000^(2i/d_model))`,
  `PE(pos,2i+1) = cos(pos / 10000^(2i/d_model))`.
- **Training:** Adam (β1 0.9, β2 0.98, ε 1e-9); learning rate
  `d_model^-0.5 · min(step^-0.5, step · warmup^-1.5)` with warmup = 4000;
  residual dropout 0.1; label smoothing 0.1.

Full details, including the big-model settings and decoding, are in
[methods.md](methods.md).

## Using this skill

- Implementing or debugging a Transformer: start with the architecture
  block above, then [methods.md](methods.md) for exact hyperparameters.
- Quoting results or ablations: [findings.md](findings.md) has all of
  Tables 2-4 with conditions (test vs dev set, checkpoint averaging).
- Note the paper's own inconsistency on EN-FR BLEU (41.8 in the abstract and
  Table 2, 41.0 in §6.1 text) - see [limitations.md](limitations.md).

## Files

| File | What it holds |
|---|---|
| [methods.md](methods.md) | Architecture, attention variants, data, batching, hardware, optimizer, regularization, decoding |
| [findings.md](findings.md) | Translation and parsing results, training cost, Table 3 ablations, attention visualizations |
| [limitations.md](limitations.md) | Stated limitations, open questions, and caveats evident from the methods |
| [glossary.md](glossary.md) | Terms used in the paper, one line each |
| [citations.md](citations.md) | How to cite the paper and its 40 references |
