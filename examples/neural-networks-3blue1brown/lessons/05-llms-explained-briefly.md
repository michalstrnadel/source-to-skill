https://www.youtube.com/watch?v=LPZh9BOjkQs

# Lesson 5 — Large Language Models explained briefly

A short, non-technical overview that bridges the MNIST lessons and the
transformer chapters.

## What an LLM is

- A sophisticated mathematical function that predicts the next word for any
  text — as a **probability for every possible next word**, not one certain
  answer.
- **Chatbot recipe:** write text describing an interaction between a user and
  a hypothetical AI assistant, append the user's input, then repeatedly
  predict what the assistant would say next.
- Sampling less likely words at random makes output look more natural; so the
  deterministic model gives different answers to the same prompt.

## Training

- Behavior is fully determined by many continuous **parameters** (weights);
  "large" = hundreds of billions of them. Nobody sets them by hand — they
  start random (gibberish output) and are refined on example text.
- One training step: feed all but the last word of an example, compare the
  prediction to the true last word, and use **backpropagation** to make the
  true word slightly more likely and all others slightly less likely.
- Repeated over many trillions of examples, predictions improve on training
  data *and* on unseen text.
- Scale: reading GPT-3's training text non-stop would take a human **over
  2,600 years**. At one billion additions/multiplications per second, the
  operations to train the largest models would take **well over 100 million
  years**.
- This is **pre-training**. Autocompleting internet text ≠ being a good
  assistant, so chatbots also get **reinforcement learning with human
  feedback** (RLHF): workers flag unhelpful or problematic predictions and the
  corrections further tune the parameters.

## Why transformers

- Training at this scale relies on **GPUs**, chips that run many operations
  in parallel — but not all models parallelize well.
- Before 2017 most language models processed text one word at a time. A
  Google team introduced the **transformer**, which takes in all the text at
  once, in parallel.
- Steps:
  1. Each word → a long list of numbers (training only works with continuous
     values), which may encode the word's meaning.
  2. **Attention** lets those lists "talk to one another" and refine meaning by
     context, in parallel (e.g. "bank" → riverbank).
  3. **Feed-forward networks** add capacity to store patterns learned in
     training.
  4. Many alternating iterations of both; finally a function on the **last**
     vector produces next-word probabilities.
- Researchers design the framework; the specific behavior **emerges** from
  the tuned parameters, which makes it very hard to explain why a model makes
  a given prediction.
