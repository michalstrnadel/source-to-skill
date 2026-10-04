https://www.youtube.com/watch?v=iv-5mZ_9CPY

# Lesson 10 — But how do AI images and videos actually work? (guest video by Welch Labs)

Guest video by Stephen Welch (Welch Labs), commissioned during 3Blue1Brown's
paternity leave. Thesis: image/video models use **diffusion**, equivalent to
Brownian motion run backwards in high-dimensional space — and the physics
yields real algorithms.

## What a video model actually does (WAN 2.1, open source)

- Generation starts from a random-number call: a pure-noise video.
- A **transformer** (same model type as LLMs) outputs a video; it is added to
  the noise and fed back in; repeat (snapshots at 5, 10, 20, 30, 40, 50
  iterations) until realistic video emerges.
- An empty prompt still yields a video (of a woman).

## Part 1 — CLIP (OpenAI, Feb 2021)

- Trained on **400 million** image–caption pairs; two models (text, image),
  each outputting a **512**-length vector.
- **Contrastive** objective (the "C"): in a batch, arrange image vectors as
  columns and text vectors as rows; maximize similarity on the diagonal
  (matching pairs) and minimize it off-diagonal.
- Similarity = **cosine similarity** (cosine of the angle; 1 when aligned).
- The shared **latent/embedding space** supports concept arithmetic: (me with
  hat) − (me without hat) best matches the word "hat" (similarity 0.165), then
  "cap", "helmet".
- Zero-shot classification: compare an image's vector with one caption per
  label; pick the highest cosine similarity.
- Limitation: CLIP only maps **into** the space; it cannot generate.

## Part 2 — Diffusion (DDPM, Berkeley 2020)

- Core idea: add noise to training images step by step until destroyed; train
  a network to reverse it.
- The naive version — predict step t−1 from step t, iterate — "really does not
  work well"; virtually no modern model does that. Two surprises in DDPM:
  1. **Noise is added during generation too.** Removing that line from Stable
     Diffusion 2 sampling turns "a tree in the desert" into a tiny, sad, blurry
     tree.
  2. **The model predicts the total noise** ε added to the clean image x₀, not
     one step's noise.

### The vector-field view (2-D toy: images as points, data on a spiral)

- Adding noise = a random walk = **Brownian motion**; the model must play
  diffusion backwards.
- Predicting the final step's noise is mathematically equivalent to predicting
  total noise ÷ number of steps; predicting the vector back to x₀ directly
  keeps the objective but **reduces training variance** → learns far more
  efficiently.
- The model learns, at each point, the direction back toward the data — a
  **score function** pointing to more likely, less noisy data.
- **Condition on time t** (t = 1 at the 100th step, 0.99 at the 99th, ...):
  coarse fields at large t, fine structure as t → 0. Essential in practice. A
  sudden "phase change" near t ≈ 0.4: the field switches from pointing at the
  spiral's center to pointing at the spiral itself.

### Why sampling noise matters

- DDPM sampling: step along the learned field, then add scaled random noise
  (shrinking over time). 64 steps; a 256-point cloud converges onto the spiral.
- Without the noise, all points rush to the center, then to one inner edge.
  The model learns the **mean** of the (Gaussian, for small steps) reverse
  distribution; to *sample* you must add zero-mean Gaussian noise. Without it
  you land on averages — and **in image space, averages look blurry**.

## DDIM — faster, deterministic

- DDPM's many steps (each a full network pass) were compute-heavy.
- DDPM sampling is a **stochastic differential equation** (field term + random
  term). Via the **Fokker–Planck equation**, a Google Brain team found an
  **ordinary** differential equation (no randomness) giving the same final
  **distribution** (not the same individual images).
- Result, **DDIM**: no noise during sampling, new step-size scaling (which
  matters a lot), high quality in far fewer steps, **no retraining**.
- WAN uses a generalization of DDIM called **flow matching**.

## Part 3 — Steering with text

- Combine: diffusion can invert the CLIP image encoder; CLIP text vectors can
  steer diffusion. OpenAI did this in 2022 (**unCLIP**, sold as **DALL·E 2**)
  with remarkable prompt adherence.
- **Conditioning**: feed the text vector as an extra model input (via
  cross-attention, adding/appending to the input, or several ways at once).
- Conditioning alone is not enough: Stable Diffusion (Heidelberg University,
  open source, similar approach) conditioned only on text gives a desert with a
  shadow but **no tree**.

### Classifier-free guidance

- Toy: spiral regions = people / dogs / cats; class-conditioned model fits
  roughly but confuses classes — matching the overall data overpowers moving
  toward a class.
- Train one model that sometimes gets **no** class info (drop it for a subset
  of examples) → you get both an unconditional and a conditional vector field.
  They agree at large t and diverge as t → 0.
- Guided direction: **(conditional − unconditional)**, amplified by a factor
  **α**, replaces the conditional vector → tight fits per class.
- Stable Diffusion: a tiny tree appears around **α ≈ 2** and grows in size and
  detail as α increases. Now essential in modern image/video models.
- **Negative prompts** (WAN): subtract the vector for an explicit list of
  unwanted features (e.g. extra fingers, walking backwards — written in
  Chinese) instead of the unconditioned output. Without it, scenes get
  cartoonish and parts stop fitting together.

## Takeaway

Since DDPM (summer 2020) progress has been blistering. The striking part is
that independently trained pieces (a CLIP-style text encoder steering a
diffusion model) fit together at all, and that simple geometric intuitions
hold in such high dimensions.
