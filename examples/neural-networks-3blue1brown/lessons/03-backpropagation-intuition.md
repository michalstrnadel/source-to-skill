https://www.youtube.com/watch?v=Ilg3gGewQ5U

# Lesson 3 — Backpropagation, intuitively (Deep Learning Chapter 3)

Backpropagation is the algorithm for computing the cost gradient — "the core
algorithm behind how neural networks learn". This lesson explains it with no
formulas; lesson 4 gives the calculus.

## Key reframe: gradient components = sensitivities

- Each gradient component's magnitude says how sensitive the cost is to that
  weight or bias.
- Example: components 3.2 and 0.1 → the cost is **32×** more sensitive to the
  first weight. ([2:04](https://www.youtube.com/watch?v=Ilg3gGewQ5U&t=124s))
- The hard part is notation and index-chasing; each individual effect is
  intuitive, there are just many layered on top of each other.

## One training example (an image of a 2) ([3:07](https://www.youtube.com/watch?v=Ilg3gGewQ5U&t=187s))

1. **Desired output nudges.** You cannot change activations directly, only
   weights and biases — but record what you *wish* would happen: the "2"
   neuron up, all others down, each nudge proportional to how far the value is
   from its target (a neuron already near 0 needs little change). ([4:09](https://www.youtube.com/watch?v=Ilg3gGewQ5U&t=249s))
2. **Three levers for raising the "2" neuron's activation:** ([4:09](https://www.youtube.com/watch?v=Ilg3gGewQ5U&t=249s))
   - increase its **bias**;
   - increase its **weights** — most effective on connections from the
     *brightest* previous neurons, since those weights are multiplied by large
     activations;
   - change the **previous layer's activations** — brighten neurons with
     positive weights, dim those with negative weights, in proportion to the
     weight size.
3. **Hebbian echo.** The biggest weight increases happen between neurons that
   are most active and the ones we want more active — loosely, "neurons that
   fire together wire together". The course flags this as a loose analogy only. ([5:10](https://www.youtube.com/watch?v=Ilg3gGewQ5U&t=310s))
4. **Propagate backwards.** Every output neuron has its own wishes for the
   second-to-last layer. Sum them (weighted by connection weights and by how
   much each output must change) → a list of desired nudges for that layer.
   Recursively apply the same process to the weights and biases feeding it,
   moving back through the network. ([7:12](https://www.youtube.com/watch?v=Ilg3gGewQ5U&t=432s))

## All training examples ([8:14](https://www.youtube.com/watch?v=Ilg3gGewQ5U&t=494s))

- Listening only to the "2" would push the net to call everything a 2. So run
  backprop for **every** example and **average** the desired changes. That
  average is (proportional to) the negative gradient.

## Stochastic gradient descent ([9:14](https://www.youtube.com/watch?v=Ilg3gGewQ5U&t=554s))

- Summing every example for every step is very slow. Instead: shuffle the
  data, split into **mini-batches** (e.g. 100 examples), take one step per
  mini-batch.
- Each step approximates the true gradient — not the most efficient downhill
  direction, but a big computational speedup.
- Picture: a drunk man stumbling quickly downhill rather than a careful man
  computing the exact slope before each slow step. ([10:17](https://www.youtube.com/watch?v=Ilg3gGewQ5U&t=617s))
- Repeating over all mini-batches converges to a local minimum = good
  performance on the training data.

## Summary as stated

Backprop determines how a single example wants to nudge each weight and bias —
direction *and* relative proportion. A true gradient step averages this over
all examples; in practice you use mini-batches.

## Practical note ([11:17](https://www.youtube.com/watch?v=Ilg3gGewQ5U&t=677s))

These methods need **a lot of labeled training data**. MNIST makes digits an
easy example; in practice, getting labeled data is a common bottleneck.
