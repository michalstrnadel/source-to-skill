# Findings

## Machine translation (§6.1, Table 2)

Test set: newstest2014. BLEU, and estimated training cost in FLOPs.

| Model | EN-DE BLEU | EN-FR BLEU | EN-DE cost | EN-FR cost |
|---|---|---|---|---|
| ByteNet | 23.75 | - | - | - |
| Deep-Att + PosUnk | - | 39.2 | - | 1.0e20 |
| GNMT + RL | 24.6 | 39.92 | 2.3e19 | 1.4e20 |
| ConvS2S | 25.16 | 40.46 | 9.6e18 | 1.5e20 |
| MoE | 26.03 | 40.56 | 2.0e19 | 1.2e20 |
| Deep-Att + PosUnk Ensemble | - | 40.4 | - | 8.0e20 |
| GNMT + RL Ensemble | 26.30 | 41.16 | 1.8e20 | 1.1e21 |
| ConvS2S Ensemble | 26.36 | 41.29 | 7.7e19 | 1.2e21 |
| **Transformer (base)** | **27.3** | **38.1** | 3.3e18 (one figure given) | |
| **Transformer (big)** | **28.4** | **41.8** | 2.3e19 (one figure given) | |

What the numbers say:

- **EN-DE:** big model 28.4 BLEU, more than 2.0 above the best earlier
  result including ensembles (ConvS2S Ensemble, 26.36). Trained 3.5 days on
  8 P100s. The base model (27.3) also beats every earlier model and
  ensemble, at 3.3e18 FLOPs - lower than any competitor's listed cost.
- **EN-FR:** big model is the best single model, beating all earlier single
  models at under 1/4 the training cost of the previous state of the art.
  The abstract and Table 2 give 41.8 BLEU; the §6.1 text says 41.0 (see
  [limitations.md](limitations.md)). The GNMT+RL (41.16) and ConvS2S
  (41.29) ensembles sit between those two figures.
- **Speed headline:** a new translation state of the art is reachable after
  as little as 12 hours on eight P100 GPUs (§1).

Conditions: base = average of last 5 checkpoints, big = last 20; beam 4,
length penalty 0.6; max output = input + 50.

## Model variations (§6.2, Table 3)

EN-DE dev set (newstest2013), no checkpoint averaging. Perplexity is
per-wordpiece, not comparable to per-word perplexity. Only changed values
are listed; everything else is the base model.

| Row | Change | PPL | BLEU | Params (M) |
|---|---|---|---|---|
| base | N 6, d_model 512, d_ff 2048, h 8, d_k = d_v 64, drop 0.1, ε_ls 0.1, 100K steps | 4.92 | 25.8 | 65 |
| A | h 1, d_k = d_v 512 | 5.29 | 24.9 | |
| A | h 4, d_k = d_v 128 | 5.00 | 25.5 | |
| A | h 16, d_k = d_v 32 | 4.91 | 25.8 | |
| A | h 32, d_k = d_v 16 | 5.01 | 25.4 | |
| B | d_k 16 | 5.16 | 25.1 | 58 |
| B | d_k 32 | 5.01 | 25.4 | 60 |
| C | N 2 | 6.11 | 23.7 | 36 |
| C | N 4 | 5.19 | 25.3 | 50 |
| C | N 8 | 4.88 | 25.5 | 80 |
| C | d_model 256, d_k = d_v 32 | 5.75 | 24.5 | 28 |
| C | d_model 1024, d_k = d_v 128 | 4.66 | 26.0 | 168 |
| C | d_ff 1024 | 5.12 | 25.4 | 53 |
| C | d_ff 4096 | 4.75 | 26.2 | 90 |
| D | dropout 0.0 | 5.77 | 24.6 | |
| D | dropout 0.2 | 4.95 | 25.5 | |
| D | ε_ls 0.0 | 4.67 | 25.3 | |
| D | ε_ls 0.2 | 5.47 | 25.7 | |
| E | learned positional embedding instead of sinusoids | 4.92 | 25.7 | |
| big | d_model 1024, d_ff 4096, h 16, drop 0.3, 300K steps | 4.33 | 26.4 | 213 |

Readings the authors draw:

- **(A) Heads at constant compute:** one head is 0.9 BLEU below the best
  setting (24.9 vs 25.8); too many heads (32) also loses quality.
- **(B) Key size:** smaller d_k hurts, which suggests computing
  compatibility is not easy and a richer function than a dot product might
  help.
- **(C) Size:** bigger models are better (d_model 1024 -> 26.0, d_ff 4096 ->
  26.2; N 2 -> 23.7).
- **(D) Regularization:** dropout is very helpful against over-fitting
  (no dropout: 24.6). Removing label smoothing improves perplexity (4.67)
  but lowers BLEU (25.3) - consistent with §5.4.
- **(E) Positional encoding:** learned embeddings are nearly identical to
  sinusoids.

## English constituency parsing (§6.3, Table 4)

WSJ Section 23, F1.

| Parser | Training | F1 |
|---|---|---|
| Vinyals & Kaiser et al. (2014) | WSJ only, discriminative | 88.3 |
| Petrov et al. (2006) | WSJ only, discriminative | 90.4 |
| Zhu et al. (2013) | WSJ only, discriminative | 90.4 |
| Dyer et al. (2016) | WSJ only, discriminative | 91.7 |
| **Transformer (4 layers)** | WSJ only, discriminative | **91.3** |
| Zhu et al. (2013) | semi-supervised | 91.3 |
| Huang & Harper (2009) | semi-supervised | 91.3 |
| McClosky et al. (2006) | semi-supervised | 92.1 |
| Vinyals & Kaiser et al. (2014) | semi-supervised | 92.1 |
| **Transformer (4 layers)** | semi-supervised | **92.7** |
| Luong et al. (2015) | multi-task | 93.0 |
| Dyer et al. (2016) | generative | 93.3 |

- Without task-specific tuning, the Transformer beats all previously
  reported models except the Recurrent Neural Network Grammar (Dyer et al.).
- Unlike RNN sequence-to-sequence models, it beats the BerkeleyParser
  (Petrov et al.) even when trained only on the 40K WSJ sentences.

## Attention visualizations (Appendix, Figures 3-5)

All from encoder self-attention in layer 5 of 6:

- **Long-distance dependency (Fig. 3):** many heads attending from
  "making" link it to its distant completion "more difficult".
- **Anaphora (Fig. 4):** two heads (5 and 6) appear to resolve "its"; their
  attention from that word is very sharp.
- **Sentence structure (Fig. 5):** different heads show distinct,
  structure-related patterns - evidence that heads specialize.

## Highlights (short quotes)

> "We propose a new simple network architecture, the Transformer, based
> solely on attention mechanisms, dispensing with recurrence and
> convolutions entirely." (Abstract)

> "Multi-head attention allows the model to jointly attend to information
> from different representation subspaces at different positions. With a
> single attention head, averaging inhibits this." (§3.2.2)

> "This hurts perplexity, as the model learns to be more unsure, but
> improves accuracy and BLEU score." (§5.4, on label smoothing)
