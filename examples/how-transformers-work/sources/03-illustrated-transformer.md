https://jalammar.github.io/illustrated-transformer/

# S3 — The Illustrated Transformer (Jay Alammar)

Written June 27, 2018 (with later 2020 and 2025 update notes). Follows the
paper's encoder-decoder translation model and its dimensions, deliberately
"oversimplifying" and introducing one concept at a time.

## Thesis

The Transformer is attention used to speed up training: its biggest benefit
is that it parallelizes. Once self-attention is understood as six
vector-level steps (and then one matrix formula), the rest of the
architecture — multi-head, positional encoding, residuals, decoder, output
layer — follows.

## Key claims and supporting points

- **Architecture at a glance.** A stack of 6 encoders and 6 decoders ("nothing
  magical about the number six"). Encoders share structure but not weights.
  Encoder = self-attention → feed-forward; decoder adds encoder-decoder
  attention between them.
- **Per-position paths.** Each word flows through its own path; paths
  interact only in self-attention, so the feed-forward step can run in
  parallel across positions. Embedding happens only in the bottom encoder;
  every encoder consumes a list of 512-d vectors, and the list length is a
  hyperparameter (roughly the longest training sentence).
- **Self-attention = how a word looks at other words.** "The animal didn't
  cross the street because it was too tired": encoding "it" in the top
  encoder (#5), attention focuses on "The Animal". Compared to an RNN's
  hidden state as the way to bake in other words.
- **Six steps for one position** (the first word, "Thinking"):
  1. Project each input x into q, k, v via trained W^Q, W^K, W^V (512 → 64;
     smaller only to keep multi-head cost roughly constant).
  2. Score = q1·k_j for every word j.
  3. Divide by 8 (sqrt of 64) — "more stable gradients".
  4. Softmax → positive weights summing to 1. The article says the word
     itself will "clearly" get the highest weight.
  5. Multiply each v by its weight (irrelevant words drowned out, e.g. ×0.001).
  6. Sum → z1, the layer's output for that position.
- **Matrix form.** Stack embeddings as rows of X; Q = XW^Q etc.; steps 2–6
  collapse into `Z = softmax(QK^T / sqrt(d_k)) V`.
- **Multi-head ("The Beast With Many Heads").** Two benefits: more ability
  to focus on different positions (z1 might otherwise be dominated by the
  word itself), and multiple representation subspaces. 8 heads → 8 Z
  matrices → concatenate → multiply by W^O → one matrix for the FFN.
  Example: for "it", one head attends to "the animal", another to "tired".
  With all 8 heads shown, it gets hard to interpret.
- **Positional encoding.** A vector added to each embedding, giving
  meaningful distances once projected to Q/K/V. Shown with a toy dimension
  of 4 and a 20 × 512 heatmap (values in [−1, 1]). Advantage: scales to
  sequences longer than any seen in training. 2020 update: the heatmap
  shown is Tensor2Tensor's version, which concatenates the sine and cosine
  halves; the paper interleaves them.
- **Residuals.** Every sub-layer (self-attention, FFN) in encoder and
  decoder has a residual connection followed by layer normalization.
- **Decoder side.** Top encoder output becomes K and V for every decoder's
  encoder-decoder attention (Q from the layer below). Decoding is a loop:
  each step emits one word, which is fed back (embedded + positional
  encoding) as input to the next step until an end symbol. Decoder
  self-attention only sees earlier positions — future positions set to −inf
  before softmax.
- **Output layer.** Final Linear projects the decoder vector to a logits
  vector the size of the vocabulary (example: 10,000 words); softmax turns it
  into probabilities; pick the highest.
- **Training and loss.** Toy vocabulary of six words with one-hot targets.
  Compare predicted and target distributions (pointer to cross-entropy and
  KL divergence) and backpropagate. Realistic vocab sizes: 30,000 or 50,000.
  Example: "je suis étudiant" → "i am a student".
- **Decoding strategies.** Greedy decoding (keep the argmax) vs beam search
  (keep top-k partial hypotheses; example beam_size = 2, top_beams = 2).

## Highlights

- "The biggest benefit, however, comes from how The Transformer lends itself
  to parallelization." (intro)
- "Self-attention is the method the Transformer uses to bake the
  “understanding” of other relevant words into the one we're currently
  processing." (Self-Attention at a High Level)
- "They're abstractions that are useful for calculating and thinking about
  attention." — on what queries, keys and values are (Self-Attention in
  Detail)
- "Notice that every position gets a little bit of probability even if it's
  unlikely to be the output of that time step -- that's a very useful
  property of softmax which helps the training process." (The Loss Function)

## Next steps it recommends

Read the paper, the Google Transformer blog post and Tensor2Tensor
announcement; watch Łukasz Kaiser's talk; use the Tensor2Tensor notebook
and repo; follow-ups include Image Transformer, Self-Attention with
Relative Position Representations, Adafactor.
