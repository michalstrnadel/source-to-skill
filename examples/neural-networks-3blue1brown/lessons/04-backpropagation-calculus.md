https://www.youtube.com/watch?v=tIeHLnjs5U8

# Lesson 4 — Backpropagation calculus (Deep Learning Chapter 4)

Assumes lesson 3. Goal: show how ML practitioners think about the chain rule
in networks. Expect confusion — pause and ponder.

## One neuron per layer

Network with three weights and three biases; focus on the last two neurons.

- Notation (superscripts are layer indices, not exponents):
  - `a(L)` last activation, `a(L-1)` previous activation, `y` desired value.
  - `z(L) = w(L)·a(L-1) + b(L)` (the weighted sum, named for convenience).
  - `a(L) = σ(z(L))` (sigmoid, ReLU, ...).
  - Cost of one example: `C0 = (a(L) − y)²`.
- Dependency chain: `w(L), a(L-1), b(L) → z(L) → a(L) → C0`.

### Chain rule

`∂C0/∂w(L) = ∂z(L)/∂w(L) · ∂a(L)/∂z(L) · ∂C0/∂a(L)`

- `∂C0/∂a(L) = 2(a(L) − y)` — proportional to the error, so a badly-wrong
  output makes small changes matter a lot.
- `∂a(L)/∂z(L) = σ'(z(L))` — derivative of the chosen nonlinearity.
- `∂z(L)/∂w(L) = a(L-1)` — a weight's effect depends on how strong the previous
  neuron is (the "fire together, wire together" idea).

### Other partials

- Bias: swap the first factor for `∂z/∂b = 1`.
- Previous activation: `∂z(L)/∂a(L-1) = w(L)`. You can't set `a(L-1)`
  directly, but tracking its sensitivity lets you iterate the same chain rule
  backwards to earlier weights and biases — the "propagating backwards".

### Averaging

The full cost averages over training examples, so its derivative averages
these per-example expressions. Each such derivative is one component of the
gradient vector.

## Many neurons per layer

Only "a few more indices":

- `k` indexes layer L−1, `j` indexes layer L; activations `a(L)_j`.
- Cost: `C0 = Σ_j (a(L)_j − y_j)²`.
- Weight from neuron k to neuron j: `w(L)_jk` (index order matches the weight
  matrix from lesson 1).
- `z(L)_j = Σ_k w(L)_jk a(L-1)_k + b(L)_j`, `a(L)_j = σ(z(L)_j)`.
- `∂C/∂w(L)_jk` has essentially the same chain-rule form.
- **What changes:** `∂C/∂a(L-1)_k` must **sum over all paths** — neuron k
  influences every `a(L)_j`, each of which affects the cost.

Once you know the cost's sensitivity to the second-to-last layer's
activations, repeat for the weights and biases feeding that layer. These
chain-rule expressions are the gradient components gradient descent uses.
