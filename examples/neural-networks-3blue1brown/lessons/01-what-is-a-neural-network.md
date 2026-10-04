https://www.youtube.com/watch?v=aircAruvnKk

# Lesson 1 — But what is a neural network? (Deep Learning Chapter 1)

Goal: understand the *structure* of a plain "vanilla" network (no frills)
that recognizes handwritten digits; learning comes in lesson 2. The plain
form is presented as the prerequisite for every modern variant.

## The task

- Input: a 28×28 grayscale image of a digit. Output: which digit (0–9).
- Writing this as an explicit program is "dauntingly difficult" even though
  brains do it effortlessly — the motivation for learning from data.

## Anatomy

- **Neuron** = a thing that holds a number between 0 and 1 (its
  **activation**). Later refined: each neuron is really a *function* of the
  previous layer's outputs.
- **Input layer**: 784 neurons (28 × 28), activation = pixel brightness
  (0 black → 1 white).
- **Output layer**: 10 neurons, one per digit; the brightest is the network's
  answer.
- **Hidden layers**: two layers of 16 neurons each — an admittedly arbitrary
  choice (16 "fit nicely on the screen"); structure is open to experiment.
- Activations in one layer determine the next, loosely analogous to
  biological neurons firing others.

## Why layers might work (the hope)

- Digits decompose into parts: 9 = upper loop + right line; 8 = two loops;
  4 ≈ three lines.
- Hope: second-to-last layer detects such sub-components; the layer before
  detects little edges; the last layer combines components into digits.
- Same layered-abstraction idea applies elsewhere, e.g. speech: raw audio →
  sounds → syllables → words → phrases → thoughts.
- (Lesson 2 shows the trained network does *not* actually do this.)

## Weights, bias, nonlinearity

- Each connection gets a **weight** (just a number). A neuron computes the
  weighted sum of all previous activations.
- Visualize a neuron's 784 weights as a pixel grid: green = positive, red =
  negative. To detect an edge in a region: positive weights in the region,
  negative weights around it — the sum is largest when the middle is bright and
  the surroundings dark.
- Squash the sum into (0, 1) with the **sigmoid** (logistic curve): very
  negative → ≈0, very positive → ≈1, steepest around 0.
- **Bias**: a number added before squashing (e.g. −10 if the neuron should
  only fire when the sum exceeds 10). Weights = *which pattern*; bias = *how
  strong before it activates*.
- Counting: 784 × 16 weights + 16 biases for the first hidden layer alone;
  ~13,000 weights and biases total — the knobs that "learning" sets.

## Compact notation

- Activations of a layer → column vector `a`. Weights → matrix `W` (row j =
  all connections into neuron j of the next layer). Biases → vector `b`.
- Layer transition: `a⁽¹⁾ = σ(W a⁽⁰⁾ + b)`, sigmoid applied element-wise.
- Benefits: simpler code and faster, because libraries heavily optimize
  matrix multiplication. "So much of machine learning" is linear algebra.

## The whole network is a function

784 numbers in → 10 numbers out, with ~13,000 parameters, iterated
matrix-vector products and sigmoids. Its complexity is reassuring: anything
simpler would have little hope of recognizing digits.

Why bother understanding individual weights: when a network misbehaves (or
works for unexpected reasons), knowing what weights and biases mean gives you
a starting point to change the structure and to challenge assumptions.

## Coda: sigmoid vs. ReLU (with Lisha Li)

- Sigmoid was used by early networks, motivated by the active/inactive neuron
  analogy; relatively few modern networks use it — "kind of old school".
- **ReLU** (rectified linear unit) = `max(0, a)`: identity above the
  threshold, zero below. Sigmoid made deep networks hard to train; ReLU
  "happened to work very well" for very deep networks.
