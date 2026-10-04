https://www.youtube.com/watch?v=IHZwWFHWa-w

# Lesson 2 — Gradient descent, how neural networks learn (Deep Learning Chapter 2)

Two goals: introduce gradient descent (which underlies far more of machine
learning than neural nets), then inspect what the trained network actually
does.

## Setup

- Training data: labeled images (MNIST — tens of thousands of labeled
  handwritten digits). Testing: show the trained net labeled images it has
  never seen and measure accuracy; the hope is that layered structure makes
  learning **generalize**.
- Start with all ~13,000 weights and biases **random** → output is a mess.

## Cost function

- Cost of one example = Σ (output activation − desired activation)²; desired
  = 1 for the correct digit's neuron, 0 elsewhere. Small when the network is
  confidently right, large when it is confused.
- Total cost = **average** over all training examples.
- Layers of abstraction: the network is a function (784 → 10); the cost is a
  function of the ~13,000 parameters → 1 number of "lousiness"; the gradient
  of the cost is one more layer still.

## Gradient descent

- 1-D intuition: find the slope, step left if positive, right if negative,
  repeat → reach a **local** minimum ("ball rolling down a hill"). Which valley
  you land in depends on the random start; no guarantee of the global minimum.
- Steps proportional to the slope shrink near the minimum and help prevent
  overshooting.
- 2-D and beyond: the **gradient** gives the direction of steepest ascent and
  its length the steepness; step along the **negative gradient**.
- Algorithm: compute the gradient, take a small step downhill, repeat. Same
  idea for 13,000 inputs: put all parameters in one column vector; the negative
  gradient says which nudges decrease cost fastest.
- Computing that gradient efficiently = **backpropagation** (lessons 3–4).
- "Learning" just means minimizing a cost function. This requires a smooth
  cost — which is why artificial neurons have continuous activations rather
  than binary on/off like biological ones.

## Reading the gradient non-spatially

- Each component's **sign** says nudge up or down; the **relative
  magnitudes** say which changes matter more.
- Example: gradient (3, 1) at a point → changing the first variable matters
  3× as much as the second, locally.

## How well it works

- The 2×16 hidden-layer network classifies about **96%** of unseen images
  correctly; with a few tweaks to the hidden structure, **98%**. Better
  architectures do better still.

## What the hidden layers actually learned

- Visualizing first-to-second-layer weights: not edges, but almost random
  patterns with loose structure in the middle — the net found a "happy little
  local minimum" that classifies well without the hoped-for features.
- Feed it random noise and it answers confidently (e.g. "5"), as sure as for a
  real 5. It can recognize digits but "has no idea how to draw them".
- Cause: a tightly constrained universe (centered, static digits in a tiny
  grid) and a cost that never rewards anything but total confidence.
- Framing: this is 80s–90s technology — a necessary starting point, not the
  end goal.
- Exercise suggested: think about what you'd change so the system picks up
  edges and patterns. Recommended resources: Michael Nielsen's free book on
  neural networks and deep learning (code and data for this exact example),
  Chris Olah's blog, Distill.

## Coda: memorization vs. structure (with Lisha Li)

- A paper trained a deep image network on **shuffled labels**: test accuracy
  was no better than random, yet training accuracy matched the properly
  labeled case — millions of weights can simply memorize.
- A follow-up (ICML): on random labels the training curve falls slowly, almost
  linearly; on properly labeled data it fiddles briefly then drops fast — the
  right minimum is easier to find when data is structured.
- An earlier paper (with simplifying assumptions): the local minima these
  networks find tend to be of equal quality.
