https://www.youtube.com/watch?v=GlYgs6v2YfU

# Lesson 9 — But what is cross-entropy? (Compression is Intelligence, Part 2)

Part 2 of a separate series; Part 1 (entropy, optimal codes) is not in this
playlist, but the needed results are restated. Thesis: cross-entropy arises
naturally in compression, is also the LLM training loss, and that shared
formula hints that training a language model is training a compressor.

## Hook: *Language Trees and Zipping* (2002)

- Cluster documents by language and even recover the tree of language lineage
  using only **gzip**, no linguistics.
- Trick: append a snippet of B to A, compress, compare with compressing A
  alone. Small difference ⇒ B's patterns resemble A's. A distance built on
  this recovered the lineage tree; the same trick works for authorship.
- It is only an empirical, rough estimate of cross-entropy (documents aren't
  distributions; gzip just replaces repeats with pointers and is far from the
  Shannon limit) — but useful.

## Information and entropy (recap)

- Robot instructions up/down/left/right with probabilities 1/2, 1/4, 1/8, 1/8:
  optimal code uses 1, 2, 3, 3 bits.
- General rule: an optimal code spends **−log₂ p** bits on a symbol (Shannon's
  **information content**; "how many times do you halve to get there").
- A message's information = sum over its symbols; optimal encoding length ≈
  that total, so fractional bits are meaningful.
- **Entropy** H(Q) = Σ qᵢ · (−log₂ qᵢ): the average bits per symbol under the
  optimal code for Q. Visualize as bars with width qᵢ, height −log₂ qᵢ.

## Cross-entropy

- New reality P: up 1/8, down 1/8, left 1/4, right 1/2, but the old code is
  hard-wired. Average cost = **2.625 bits/symbol** — the cross-entropy.
- Definition: **H(P, Q) = Σ pᵢ · (−log₂ qᵢ)** — average bits when reality is P
  but the code is optimized for Q. Bars: width pᵢ, height −log₂ qᵢ. Notation
  conventions in the wild vary; think about the sum itself.
- Order matters:
  - Q = 50/50, P = 90/10 → H(Q) = 1 bit, cross-entropy = 1 bit (every symbol
    costs 1 bit, so weights don't matter).
  - Q = 90/10, P = 50/50 → H(Q) < 1 bit, but cross-entropy ≈ **1.74 bits**.
- **Key property:** fix P, vary Q → cross-entropy is minimized exactly when
  **Q = P**, and that minimum equals **H(P)**. (Traced over all P, the minima
  draw the entropy curve.)
- General use: quantify how different the patterns of one setting are from
  another's.

## Pre-training loss

- An LM maps any token sequence to a distribution over the next token. Train
  with a loss; once the loss is defined, gradient descent and backprop "take it
  from there" — the engineer's key design question is the loss.
- Loss = **average information per token from the model's perspective**: for
  every prefix in the data, take −log(probability the model gave the true next
  token), average over all tokens in the training set. Models produce all these
  probabilities in one pass.
- A smart model is rarely surprised (low loss); a confused one is surprised
  constantly; −log punishes very low probabilities steeply.
- ML uses the **natural log**: differs from log₂ by a constant absorbed into
  the learning rate, and derivatives are cleaner.
- Minimizing it ideally approaches the **entropy of language**, leaving a
  powerful general predictor. Glossed over: batching, optimizers, engineering at
  scale.

## Why it's called cross-entropy (and why log is forced)

- The common explanation — cross-entropy against a one-hot distribution on the
  true token, which collapses to −log q — is unsatisfying: it doesn't explain
  *why*.
- Better: take a context like "My name is ___" that appears many times. Let Q
  be the model's distribution and P the frequency of each name in the data.
  The average loss over all instances = Σ pᵢ · F(qᵢ) for some decreasing loss
  function F.
- With F = −log, this **is** the cross-entropy of the model relative to the
  data, minimized exactly when model = data statistics.
- Conversely, if you demand the average loss be minimized **only** when the
  model matches the data, a Lagrange-multiplier argument (minimize subject to
  Σqᵢ = 1) forces F′(q) ∝ 1/q — **only logarithms** qualify. "Your hand is
  forced."

## Distillation

- Train a small model to mimic a big one: at each token, loss = cross-entropy
  of the small model's full distribution relative to the big model's full
  distribution, rather than against the single true next token.
- Much richer signal: like learning chess from a stronger player weighing all
  good moves versus watching one game. For "My name is ___", one example
  already carries a whole reasonable name distribution.

## KL divergence

- **KL(P‖Q) = cross-entropy − entropy of P**: bits per symbol wasted by using a
  poorly optimized code. (Robot example, derived from the numbers above:
  2.625 − 1.75 = 0.875 bits.)
- Acts as a distance between distributions: zero when equal, grows as they
  differ, but **asymmetric**.
- Exercises posed: show the compact KL formula equals the difference form;
  interpret the KL bar diagram; what would happen if distillation used KL
  divergence instead of cross-entropy?

## Coming next (not in playlist)

Turning a predictor into a compressor (bits ≈ the text's information content
from the model's perspective), which makes cross-entropy training equivalent
to training the best text compressor — the basis for "compression is
intelligence".
