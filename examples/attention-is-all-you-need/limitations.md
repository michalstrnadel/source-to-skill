# Limitations and caveats

## Stated by the authors

- **Quadratic cost in sequence length.** Self-attention is O(n²·d) per
  layer; it is only cheaper than recurrence when n < d. For very long
  sequences the authors suggest restricting attention to a neighborhood of
  size r, at the price of a longer maximum path length O(n/r) - proposed,
  not tested (§4, Table 1).
- **Reduced effective resolution.** Averaging over attention-weighted
  positions blurs detail; multi-head attention is the counter-measure, not
  a proof that the loss disappears (§2).
- **Dot-product compatibility may be too weak.** Shrinking d_k hurts
  quality, which the authors read as a sign that a more sophisticated
  compatibility function could help (§6.2, rows B).
- **Too many heads hurts** - quality drops at 32 heads (§6.2, rows A).
- **Label smoothing trades perplexity for BLEU** (§5.4).
- **Open directions (§7):** other modalities (images, audio, video), local
  or restricted attention for large inputs and outputs, and less sequential
  generation - the decoder is still auto-regressive, one token at a time.

## Evident from the methods

- **Inconsistent EN-FR headline.** The abstract and Table 2 give 41.8 BLEU
  for Transformer (big) on EN-FR; §6.1 says 41.0. Both appear in the
  extracted v7 text. Quote the number with its location, and do not merge
  them.
- **Narrow evaluation.** Two WMT 2014 language pairs plus one parsing task;
  all ablations are on a single dev set (EN-DE newstest2013) and use one
  run per configuration, with no variance or significance reported.
- **Ablation conditions differ from headline results.** Table 3 uses no
  checkpoint averaging and the dev set; Table 2 uses checkpoint averaging
  and the test set. Do not compare their BLEU values directly.
- **Training cost is an estimate.** FLOPs are training time x GPU count x
  an assumed sustained throughput per GPU type, not measured compute
  (footnote 5), and baselines' costs depend on the same approximations.
- **Decoding hyperparameters were tuned on dev** (beam size, length
  penalty; and for parsing, dropout, learning rate and beam size on
  Section 22), so test results include that light tuning.
- **Positional-encoding extrapolation is a hypothesis.** Sinusoids were
  chosen because they *may* extrapolate to longer sequences; the paper does
  not test sequences longer than those seen in training.
- **Interpretability evidence is anecdotal.** The attention-head analysis
  is a handful of visualized examples from one layer, not a systematic
  study.
- **Parsing is not state of the art overall.** The Recurrent Neural Network
  Grammar (93.3, generative) and multi-task Luong et al. (93.0) score
  higher.
- **Perplexities are per-wordpiece** and not comparable to per-word
  perplexities elsewhere (Table 3 caption).
