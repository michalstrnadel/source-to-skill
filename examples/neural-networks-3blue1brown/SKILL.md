---
name: neural-networks-3blue1brown
description: Course skill distilled from 3Blue1Brown's "Neural networks" YouTube playlist (10 videos) - from a plain MNIST digit classifier (neurons, weights, biases, sigmoid/ReLU), through cost functions, gradient descent, stochastic gradient descent and backpropagation with its chain-rule calculus, to large language models and transformers (tokens, embeddings, softmax and temperature, attention heads with query/key/value, masking, MLP blocks storing facts, superposition, the full GPT-3 175B parameter tally), cross-entropy loss, KL divergence and distillation, and diffusion image/video models (CLIP, DDPM, DDIM, classifier-free guidance). Load when explaining or teaching how neural networks, backprop, transformers, attention, LLM training losses or diffusion models work, when someone needs an intuition-first mental model or a concrete number (e.g. GPT-3 dimensions), or asks "what does this 3Blue1Brown lesson say about X".
---

# Neural networks — 3Blue1Brown (course skill)

Source: https://www.youtube.com/playlist?list=PLZHQObOWTQDNU6R1_67000Dx_ZCJB-3pi
(channel: 3Blue1Brown, 10 videos). Lesson 10 is a guest video by Welch Labs;
lesson 9 is "Part 2" of a separate *Compression is Intelligence* series (its
Part 1 is not in this playlist). Transcripts carry no timestamps, so lesson
files link to the whole video.

## What the course teaches, in order

1. **Structure** (L1) — a network is just a function: 784 pixel inputs →
   10 digit outputs, built from weighted sums + bias + a squishing
   nonlinearity, compactly `a' = σ(W a + b)`.
2. **Learning = minimizing a cost** (L2) — define a cost over all training
   data, follow the negative gradient downhill.
3. **Backpropagation** (L3 intuition, L4 calculus) — how one training example
   "wants" every weight and bias nudged; average those wishes; use
   mini-batches (SGD) for speed.
4. **LLMs in brief** (L5) — next-word prediction, pre-training, RLHF, GPUs and
   why transformers parallelize.
5. **Transformers** (L6) — tokens → embeddings → alternating attention/MLP
   blocks → unembedding → softmax; deep-learning's "format rules".
6. **Attention** (L7) — query/key dot products → softmax'd, masked attention
   pattern → value vectors added to embeddings; multi-head.
7. **MLPs store facts** (L8) — up-projection + ReLU acts like AND-gates on
   feature directions; down-projection adds the associated fact; superposition.
8. **Cross-entropy** (L9) — from compression ("bits wasted by the wrong
   code") to the LLM loss; why the log is forced; distillation; KL divergence.
9. **Diffusion** (L10) — CLIP's shared text/image space, DDPM as reversed
   Brownian motion, DDIM, conditioning and classifier-free guidance.

## Core mental models (front-loaded)

- **A neuron holds a number; a network is a function.** Each neuron's
  activation = nonlinearity(weighted sum of previous layer + bias). Weights
  pick the pattern; the bias sets how high the sum must be before the neuron
  is meaningfully active. The 784-16-16-10 MNIST net has ~13,000 parameters.
- **Learning is calculus, not magic.** Cost of one example = sum of squared
  differences between output and target; total cost = average over all
  examples. The negative gradient tells each parameter which way to move *and*
  how much it matters (relative magnitudes = "bang for your buck").
- **Smoothness is required.** Gradient descent needs a smooth cost, which is
  why artificial neurons have continuous activations instead of on/off.
- **Backprop = recursively summed wishes.** Output errors set desired nudges;
  each neuron's wish is split across bias, weights (proportional to the
  previous activation — "fire together, wire together") and previous-layer
  activations (proportional to the weights); wishes from all output neurons
  are summed, then the process repeats one layer back.
- **Chain rule per weight:** `∂C/∂w(L) = a(L-1) · σ'(z(L)) · 2(a(L) − y)`;
  for the bias the first factor is 1; for the previous activation it is
  `w(L)`, and with many neurons you sum over every path to the cost.
- **Deep learning's format**: inputs and every layer are arrays of real numbers
  (tensors); parameters ("weights") touch data only through weighted sums
  (matrix-vector products); nonlinearities carry no parameters. Keep weights
  (the learned "brains") distinct from the data flowing through.
- **Directions carry meaning.** Embedding differences encode concepts
  (woman − man ≈ a gender direction; cats − cat ≈ plurality). Dot products
  measure alignment: positive = similar, 0 = perpendicular, negative = opposite.
- **Attention moves information between positions; MLPs don't.** Attention
  lets vectors update each other by context; the MLP processes every vector
  independently and in parallel and holds ~2/3 of GPT-3's parameters.
- **High dimensions hold far more "nearly perpendicular" features than
  dimensions** (Johnson–Lindenstrauss), so features likely live in
  superposition across neurons — one reason models are hard to interpret and
  scale well.
- **Cross-entropy is the forced choice of loss.** If you want the average loss
  minimized exactly when the model's distribution matches the data's, the
  per-token loss must be −log q. Minimum value = entropy of the data; the gap
  is the KL divergence.
- **Diffusion models learn a time-conditioned vector field** pointing from
  noisy data back toward the data distribution; sampling follows it backward.

## GPT-3 by the numbers (from L5–L8)

- Vocabulary 50,257 tokens; embedding dimension 12,288; context 2,048 tokens.
- 175B weights in just under 28,000 matrices, in 8 categories.
- Embedding `W_E` ≈ 617M; unembedding `W_U` ≈ 617M.
- Attention: key/query space 128-dim; ~6.3M params per head; 96 heads per
  block → ~600M per block; 96 layers → just under 58B (about 1/3 of total).
- MLP: hidden size just under 50,000 (exactly 4 × 12,288); up + down ≈ 1.2B
  per block; 96 blocks → ~116B (about 2/3 of total).
- Normalization and bias parameters: a trivial share.
- Training compute: at 1 billion operations/second, training the largest
  models would take well over 100 million years (L5); a human reading GPT-3's
  training text 24/7 would need over 2,600 years.

## Lesson index

| # | Lesson | One-line takeaway | File |
|---|--------|-------------------|------|
| 1 | But what is a neural network? (Ch. 1) | Layers of weighted sums + bias + sigmoid; the whole net is a 13k-parameter function | [lessons/01-what-is-a-neural-network.md](lessons/01-what-is-a-neural-network.md) |
| 2 | Gradient descent, how neural networks learn (Ch. 2) | Learning = minimizing average cost along the negative gradient; ~96–98% on MNIST, but hidden layers don't find "edges" | [lessons/02-gradient-descent.md](lessons/02-gradient-descent.md) |
| 3 | Backpropagation, intuitively (Ch. 3) | Each example's desired nudges propagate backward and are averaged; mini-batches give SGD | [lessons/03-backpropagation-intuition.md](lessons/03-backpropagation-intuition.md) |
| 4 | Backpropagation calculus (Ch. 4) | Chain rule through z → a → C; sum over paths for multi-neuron layers | [lessons/04-backpropagation-calculus.md](lessons/04-backpropagation-calculus.md) |
| 5 | Large Language Models explained briefly | Next-word probability machine; pre-training + RLHF; transformers parallelize | [lessons/05-llms-explained-briefly.md](lessons/05-llms-explained-briefly.md) |
| 6 | Transformers, the tech behind LLMs (Ch. 5) | Tokens → embeddings → attention/MLP stack → unembedding → softmax (with temperature) | [lessons/06-transformers.md](lessons/06-transformers.md) |
| 7 | Attention in transformers, step-by-step (Ch. 6) | softmax(QKᵀ/√d) with causal mask weights value vectors added to embeddings; 96 heads × 96 layers | [lessons/07-attention.md](lessons/07-attention.md) |
| 8 | How might LLMs store facts (Ch. 7) | MLP = up-projection, ReLU AND-gate, down-projection adding a fact direction; superposition | [lessons/08-mlps-store-facts.md](lessons/08-mlps-store-facts.md) |
| 9 | But what is cross-entropy? (Compression is Intelligence, Pt. 2) | Cross-entropy = cost of using the wrong code; it is the only loss minimized at model = data | [lessons/09-cross-entropy.md](lessons/09-cross-entropy.md) |
| 10 | But how do AI images and videos actually work? (guest: Welch Labs) | CLIP + diffusion as reversed Brownian motion; noise during sampling, DDIM, classifier-free guidance | [lessons/10-diffusion-models.md](lessons/10-diffusion-models.md) |

Cross-lesson rules, formulas and techniques: [cheatsheet.md](cheatsheet.md).

## How to use this skill

- Concept question → answer from the mental models above, then open the one
  lesson file that covers it for detail and the video link.
- "How many parameters / what dimension" → GPT-3 section above, then L6–L8.
- Building an explanation for a learner → follow the course order; the
  course deliberately teaches the plain MNIST network first because every
  later piece (MLP blocks, backprop at scale) reuses it.
- Caveat: the MNIST net, GPT-3 figures and examples are the course's teaching
  choices (the MNIST net is, in the course's words, 80s/90s-era technology;
  GPT-3 is used because its numbers are public); the course itself notes
  modern models are bigger and their numbers mostly unpublished.
