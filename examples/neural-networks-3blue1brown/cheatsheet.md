# Cheatsheet — Neural networks (3Blue1Brown)

Lesson tags like (L3) point to `lessons/NN-*.md`.

## Formulas

- Layer transition: `a' = σ(W a + b)`, nonlinearity element-wise (L1).
- Sigmoid: squashes ℝ to (0, 1). ReLU: `max(0, x)`. GELU: smoother ReLU (L1, L8).
- Per-example squared-error cost: `C0 = Σ_j (a_j − y_j)²`; total cost = mean
  over examples (L2).
- Gradient descent step: `θ ← θ − η ∇C(θ)`, step ∝ slope (L2).
- Backprop, last layer: `∂C0/∂w(L) = a(L-1) · σ'(z(L)) · 2(a(L) − y)`;
  `∂z/∂b = 1`; `∂z/∂a(L-1) = w(L)`; sum over all paths when a neuron feeds
  several outputs (L4).
- Softmax: `softmax(x)_i = e^{x_i/T} / Σ_j e^{x_j/T}`; inputs are **logits**;
  T = temperature (L6).
- Attention: `softmax(QKᵀ / √d_k) V`, column-wise softmax, causal mask = −∞
  before softmax (L7).
- MLP block: `E + W_down · ReLU(W_up E + b_up) + b_down` (L8).
- Information content: `−log₂ p`. Entropy `H(P) = Σ pᵢ(−log₂ pᵢ)`.
  Cross-entropy `H(P,Q) = Σ pᵢ(−log₂ qᵢ)`. `KL(P‖Q) = H(P,Q) − H(P)` (L9).
- LM pre-training loss: mean over tokens of `−ln q(true next token)` (L9).
- Classifier-free guidance: take `v_cond − v_uncond`, amplify by α, and use
  that direction in place of `v_cond` (commonly written
  `v_uncond + α (v_cond − v_uncond)`) (L10).

## Procedures

**Train a network with SGD (L2–L3)**
1. Initialize all weights and biases randomly.
2. Shuffle training data; split into mini-batches (e.g. 100 examples).
3. For each mini-batch: forward pass → cost → backprop each example's desired
   nudges → average → step down the negative gradient.
4. Repeat over all mini-batches until cost converges to a local minimum.
5. Evaluate on labeled data the network has never seen.

**Generate text with an LLM (L5–L6)**
1. Tokenize; prepend a system prompt framing a user/assistant dialogue.
2. Embed → alternate attention and MLP blocks → unembed last vector → softmax.
3. Sample a token (temperature controls randomness), append, repeat.

**One attention head (L7)**: queries `W_Q e`, keys `W_K e` → dot-product grid
→ ÷√d → mask → column softmax → weight value vectors → sum → add Δe to e.

**DDPM sampling (L10)**: start from noise → step along the model's
time-conditioned field → add scaled Gaussian noise (shrinking) → repeat.
**DDIM**: same trained model, no added noise, different step scaling, far fewer
steps, deterministic.

**Distillation (L9)**: per token, loss = cross-entropy of the small model's
distribution relative to the big model's full distribution.

## Decision rules and diagnostics

- Read a gradient component's sign as up/down and its magnitude as importance:
  3.2 vs 0.1 → cost is 32× more sensitive to the first (L3).
- Need a smooth cost to descend → use continuous activations (L2).
- Deep networks hard to train with sigmoid → ReLU trained well for very deep
  nets (L1).
- Full-batch gradient too slow → mini-batches (stochastic gradient descent) (L3).
- Confident answers on random noise = sign the training setup only ever
  rewarded confidence, not understanding (L2).
- High training accuracy doesn't prove structure was learned: networks can
  memorize shuffled labels; structured data trains much faster (L2).
- Need values to form a distribution → softmax; need more diverse samples →
  raise temperature (risk: nonsense); need predictability → T → 0 (L6).
- Prevent later tokens leaking into earlier predictions → mask with −∞
  *before* softmax, not 0 after (L7).
- Context length is costly because attention is context² in size (L7).
- Value map too large (d×d) → factor it low-rank (down then up) (L7).
- Want the loss minimized only when model = data → the loss must be −log (L9).
- Training a small model when a big one exists → distill against full
  distributions, not one-hot targets (L9).
- Generated images blurry → you may be landing on the mean; add sampling noise
  (DDPM) or use proper ODE step scaling (DDIM) (L10).
- Text conditioning ignored (object missing) → classifier-free guidance; raise
  α; use a negative prompt to steer away from artifacts (L10).

## Named techniques and terms

Activation · weights · bias · sigmoid · ReLU · GELU · MNIST · cost function ·
gradient descent · local minimum · backpropagation · chain rule · Hebbian
"fire together, wire together" · mini-batch · stochastic gradient descent ·
tensor · token · embedding (`W_E`) · unembedding (`W_U`) · context size ·
softmax · temperature · logits · system prompt · pre-training · RLHF ·
attention head · query/key/value · attention pattern · masking ·
self- vs cross-attention · multi-head attention · output matrix · MLP /
feed-forward · up/down projection · superposition · Johnson–Lindenstrauss ·
sparse autoencoder · information content · entropy · cross-entropy ·
KL divergence · distillation · CLIP · contrastive learning · cosine
similarity · DDPM · score function · time conditioning · SDE / ODE ·
Fokker–Planck · DDIM · flow matching · conditioning · classifier-free
guidance · negative prompt.

## Numbers worth remembering

- MNIST net: 784 → 16 → 16 → 10, ~13,000 params, ~96% test accuracy (98%
  with tweaks) (L1–L2).
- GPT-3: 175B params, ~28,000 matrices in 8 categories, vocab 50,257, d_model
  12,288, context 2,048, 96 layers, 96 heads/layer, key/query dim 128, MLP
  hidden ≈ 4 × 12,288 (L6–L8).
- GPT-3 split: embed 617M + unembed 617M + attention ~58B (≈1/3) + MLP ~116B
  (≈2/3) (L6–L8).
- Superposition demo: 10,000 vectors in 100 dims, all pairwise angles within
  89°–91° after optimization (L8).
- Robot code: 2.625 bits/symbol under the shifted distribution; 90/10 code on
  50/50 data ≈ 1.74 bits (L9).
- CLIP: 400M image–caption pairs, 512-dim vectors (L10).
- Stable Diffusion: tree appears at guidance α ≈ 2 (L10).
