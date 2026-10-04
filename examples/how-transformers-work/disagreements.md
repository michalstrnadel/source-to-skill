# Disagreements and differing framings

S1 = paper (Vaswani et al. 2017), S2 = 3Blue1Brown video (2024),
S3 = Illustrated Transformer (Alammar 2018). The three sources agree on the
core formula `softmax(QK^T / sqrt(d_k)) V`. They differ in what they model
(encoder-decoder translation vs a decoder-only GPT), in notation, and in
which part of the story they treat as essential. Each point gives every
position separately. None of them is averaged into one claim.

## Genuine contradictions

### 1. Are positional encodings learned or fixed?
- **S1:** fixed sine/cosine functions (§3.5). Learned positional embeddings
  were tried as an ablation and scored about the same (25.7 vs 25.8 BLEU,
  Table 3 E). The paper chose sinusoids because they may extrapolate to
  longer sequences.
- **S3:** says the added vectors "follow a specific pattern that the model
  learns". The same section then shows the paper's fixed formula and
  credits it with scaling to unseen lengths, so the article contradicts
  itself here.
- **S2:** does not choose a side. It says the embedding "also encodes the
  position" and leaves the method for later.
- **Use:** S1's definition. The original Transformer uses **fixed**
  encodings, and learned ones are an alternative that works about as well.

### 2. Sine/cosine layout inside the encoding vector
- **S1:** interleaved. Even dimensions use sin and odd dimensions use cos
  (PE(pos,2i) and PE(pos,2i+1)).
- **S3 (original figure):** the left half is sine and the right half is
  cosine, concatenated. A July 2020 note in S3 explains that this figure
  came from the Tensor2Tensor code and that the paper interleaves the two.
- **Use:** the paper's interleaved layout is canonical. The concatenated
  layout is an implementation variant, and a model has to be trained and
  run with the same one.

### 3. The paper's own EN-FR BLEU number
- **S1 abstract and Table 2:** 41.8 BLEU for the big model on EN-FR.
- **S1 §6.1 text:** "achieves a BLEU score of 41.0".
- The disagreement is inside S1 itself. Cite 41.8 with Table 2 as the
  source, and mention the discrepancy if precision matters.

### 4. Does a word attend mostly to itself?
- **S3:** in step 4 of its walkthrough, says the word at the current
  position will "clearly" have the highest softmax score. Attending to
  other words is presented as the useful exception.
- **S2:** in its central example, the "creature" column puts most of its
  weight on "fluffy" and "blue", and the other entries are near zero. It
  describes a head whose purpose is to look at *other* tokens.
- **S1:** makes no such claim. Figures 3–5 show heads attending to
  distant words ("making" → "more difficult", "its" → "Law").
- **Takeaway:** self-dominance is not a general property of attention.
  Some heads behave that way and others (S1's figures, S2's example) do
  not. S3's "clearly" is a simplification.

## Different notation and conventions

### 5. Rows vs columns: which axis does softmax run along?
- **S1 / S3:** the matrix form is `softmax(QK^T)` with Q packed as rows
  (S3: "every row in the X matrix corresponds to a word"). Softmax runs
  across each **row**, which holds one query's scores against all keys.
- **S2:** draws the grid with queries as **columns** and keys as rows. It
  says softmax "is meant to be understood to apply column by column", and
  masking zeroes the entries where later tokens would influence earlier
  ones.
- These are the same computation transposed. Before writing code from
  S2's picture, transpose it: in `QK^T`, normalize over the key axis (last
  dim).

### 6. Who "attends to" whom?
- **S2:** when the key for "fluffy" aligns with the query for "creature",
  S2 says "the embeddings of fluffy and blue attend to the embedding of
  creature".
- **S1 / S3:** use the opposite direction. The position that issues the
  query attends to the others: encoder-decoder attention allows "every
  position in the decoder to attend over all positions in the input
  sequence" (S1), and when encoding "it" a head is
  "focusing on 'the animal'" (S3).
- **Use:** S1's convention, *query attends to key*. S2's wording is
  reversed relative to the paper and most code.

### 7. What is "the value matrix"?
- **S1:** per head, W_i^V ∈ R^(d_model × d_v) (512 → 64). One output
  matrix W^O ∈ R^(h·d_v × d_model) is applied after the heads are
  concatenated.
- **S3:** same as S1. Values are 64-d, and W^O condenses the 8 heads.
- **S2:** conceptually, the value map goes from the embedding space back
  to the embedding space (12,288 → 12,288), and the value vector "lives in
  the same very high-dimensional space as the embeddings". It is factored
  into "value down" (to 128) and "value up" (back to 12,288). S2 names
  these itself and says the names are not conventional. The "value up"
  halves of all heads, stacked together, are the paper's W^O. S2 calls
  this framing less confusing, and says the standard framing is "a little
  more conceptually confusing".
- **Use:** S1's names in code and when talking to other people. Reach for
  S2's per-head low-rank picture when explaining what a head *writes*.

### 8. Combining heads: concatenate or sum?
- **S1 / S3:** `Concat(head_1, …, head_h) W^O`.
- **S2:** each head proposes a change Δe per position, and the proposals
  are **summed** and added to the embedding.
- These are mathematically the same. Concatenating and then multiplying by
  W^O equals summing each head's output times its own block of W^O, and
  that block is S2's "value up". The two framings are equivalent, so there
  is no contradiction.

### 9. Is the attention output the new vector or a delta?
- **S2:** attention outputs Δe, which is *added to* the original embedding.
  The residual is part of what attention means in S2's explanation.
- **S1:** the sub-layer output passes through `LayerNorm(x + Sublayer(x))`.
  The residual is a separate wrapper around attention.
- **S3:** the self-attention output z goes on to the FFN. Residuals are
  introduced later as "one detail".
- **Effect:** S2 makes the residual stream central, while S1 and S3 treat
  it as plumbing. S2 also never mentions layer norm.

## Different numbers (and why)

### 10. Example dimensions

| quantity | S1 (base) | S3 | S2 (GPT-3) |
|---|---|---|---|
| embedding / d_model | 512 | 512 | 12,288 |
| query/key dim | 64 | 64 | 128 |
| value dim per head | 64 | 64 | 128 (value-down), output 12,288 |
| heads per layer | 8 | 8 | 96 |
| layers | 6 enc + 6 dec | 6 + 6 | 96 (decoder-only) |
| sqrt(d_k) divisor | 8 | 8 (stated) | not given numerically |
| vocabulary | ~37,000 BPE (EN-DE), 32,000 (EN-FR) | 10,000 example; 6 in toy; "30,000 or 50,000" realistic | not discussed |

None of these conflict, because they describe different models. S1 and S3
use the same model. S2's numbers come from GPT-3. The big model in S1 has
d_model 1024 and h = 16. Note that S2's ratio, d_model / h = 12,288 / 96 =
128, follows the same d_k = d_model / h rule as S1 (512 / 8 = 64).

### 11. Parameter counts
- **S1:** whole-model counts. Base is 65M and big is 213M (Table 3), with
  no breakdown by component.
- **S2:** a per-component count. About 6.3M per head, about 600M per
  attention block, and just under 58B for all attention, which is about a
  third of GPT-3's 175B. Most parameters sit outside attention.
- The two are on different scales and do not conflict. Only S2 shows that
  attention is a minority of the parameters.

## Different explanations of the same mechanism

### 12. What are Q, K and V?
- **S1:** defines them abstractly. Attention maps "a query and a set of
  key-value pairs to an output", using a "compatibility function" between
  the query and each key. The paper gives no intuition beyond that.
- **S2:** a story. The query is a question ("any adjectives in front of
  me?"), the key is an answer ("I'm an adjective, here"), and the value is
  *what to add* to the asker's meaning. S2 warns that this story is made
  up and that real heads are hard to interpret.
- **S3:** declines to give an intuition. Q, K and V are "abstractions that
  are useful for calculating and thinking about attention", and their roles
  are left to show themselves in the six computational steps.

### 13. Why divide by sqrt(d_k)?
- **S1:** a variance argument. With unit-variance components, q·k has
  variance d_k, so large values push softmax into regions with very small
  gradients. Unscaled dot-product attention lost to additive attention at
  large d_k.
- **S3:** "leads to having more stable gradients", and "there could be
  other possible values here, but this is the default".
- **S2:** "for numerical stability", called "a small technical detail".
- **Note:** S1's reason is about **gradients**, meaning softmax saturation.
  S2's "numerical stability" can be read as floating-point overflow, which
  is not the reason the paper gives.

### 14. Why mask?
- **S1:** to keep the model **auto-regressive**. Prediction i may depend
  only on outputs before i. The paper frames masking as a decoder property,
  combined with shifting the outputs right by one.
- **S2:** training **efficiency**. Each passage trains next-token
  prediction for every prefix at once, so later tokens must not leak the
  answer. S2 notes that masking is applied always in GPT, even when the
  model runs as a chatbot.
- **S3:** describes the mechanism (attend only to earlier positions, −inf
  before softmax) in decoder terms.
- These are complementary rationales. S1 states the constraint, and S2
  explains why the constraint pays off in training throughput.

### 15. Why multiple heads?
- **S1:** a single head averages, which reduces resolution. Multiple heads
  "jointly attend to information from different representation subspaces
  at different positions". Empirically, 1 head is 0.9 BLEU worse, and too
  many heads (32) also hurts.
- **S2:** there are many different ways context changes meaning
  (grammatical, like adjective → noun, or associative, like "Harry" near
  "wizard" vs "Queen"), and each needs its own K/Q/V maps.
- **S3:** two benefits. Heads can focus on different positions, since a
  single head's output may be dominated by the word itself. Heads also
  provide multiple representation subspaces.
- Only S1 has data showing that more heads is not always better.

### 16. Cross-attention vs encoder-decoder attention
- **S1 / S3:** named "encoder-decoder attention". Queries come from the
  decoder, and keys **and values** come from the encoder output. It is
  central to the architecture.
- **S2:** named "cross-attention" and called "not relevant" to the GPT
  example. Keys come from one data source and queries from another (S2
  does not specify where values come from), and there is typically no
  masking.
- Same mechanism under different names. Its importance differs because S2
  treats a decoder-only model.

## Different "key insight"

- **S1:** removing recurrence. The aims are parallel training (O(1)
  sequential operations) and short paths between distant positions (O(1)
  maximum path length), and the evidence is state-of-the-art BLEU at a
  fraction of the FLOPs.
- **S2:** attention as **context-dependent refinement of embeddings**. It
  moves meaning between token vectors, and the last vector must absorb
  everything needed to predict the next token. In its closing, S2 adds
  that much of attention's success comes from parallelizability rather
  than from any specific behavior.
- **S3:** **parallelization** as the biggest benefit (stated in the intro).
  The bulk of the article covers data flow through the full
  encoder-decoder, including the output layer, loss and beam search, which
  S1 only lists as hyperparameters and S2 leaves out.
- **Scope gap:** only S1 covers training recipes (Adam schedule, warmup,
  label smoothing, checkpoint averaging). Only S3 explains decoding
  strategies. Only S2 counts parameters by component and discusses the
  quadratic context cost as a practical bottleneck. S1 gives the O(n²·d)
  complexity but frames it as cheaper than RNNs when n < d.
