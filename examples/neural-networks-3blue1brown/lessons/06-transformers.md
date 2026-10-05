https://www.youtube.com/watch?v=wjZofJX0v4M

# Lesson 6 — Transformers, the tech behind LLMs (Deep Learning Chapter 5)

GPT = **Generative Pretrained Transformer**: generates text; pretrained on
massive data (with room to fine-tune); the transformer is the core invention
behind the AI boom. This chapter covers the start and end of the network plus
background; attention is the next chapter.

## Uses of transformers ([1:01](https://www.youtube.com/watch?v=wjZofJX0v4M&t=61s))

Speech → text, text → speech, text → image (DALL-E, Midjourney, 2022), and the
original 2017 Google transformer for translation. Focus here: the
ChatGPT-style model predicting the next chunk of text as a probability
distribution.

## Generation = predict, sample, append, repeat

- Prediction becomes generation by sampling from the distribution, appending
  the sample, and rerunning. ([2:02](https://www.youtube.com/watch?v=wjZofJX0v4M&t=122s))
- Demo: GPT-2 (run locally) produced an incoherent story; GPT-3 — "the same
  basic model, just much bigger" — produced a sensible one.
- Chatbot: a **system prompt** sets up a user talking to a helpful assistant;
  the user's message follows; the model predicts the assistant's reply. (An
  extra training step is needed to make this work well.) ([6:09](https://www.youtube.com/watch?v=wjZofJX0v4M&t=369s))

## Data flow, high level ([3:03](https://www.youtube.com/watch?v=wjZofJX0v4M&t=183s))

1. Split input into **tokens** (words, word pieces, common character
   combinations; image patches or sound chunks for other media).
2. Each token → a **vector**; similar meanings land close together.
3. **Attention block**: vectors exchange information to update meanings
   (e.g. "model" in "machine learning model" vs "fashion model"). ([4:04](https://www.youtube.com/watch?v=wjZofJX0v4M&t=244s))
4. **Multi-layer perceptron / feed-forward** block: no cross-talk; each vector
   goes through the same operation in parallel — like asking each vector a
   long list of questions and updating based on the answers.
5. Repeat attention ↔ MLP (with normalization steps between).
6. The last vector should hold the passage's essential meaning; an operation
   on it gives a distribution over all possible next tokens.

## Deep learning's ground rules

- Machine learning: instead of coding a procedure explicitly, set up a flexible
  structure with tunable parameters and fit them to examples. Simplest case:
  linear regression (two parameters: slope and intercept, e.g. house size →
  price). GPT-3 has 175 billion. ([7:11](https://www.youtube.com/watch?v=wjZofJX0v4M&t=431s))
- It is not a given that a huge model won't overfit or be intractable to train;
  deep learning is the class of models shown to **scale remarkably well**, all
  trained with **backpropagation**, which imposes a format: ([9:13](https://www.youtube.com/watch?v=wjZofJX0v4M&t=553s))
  - input is an array of real numbers (a **tensor**), transformed layer by
    layer, each layer also an array of reals, until the output layer;
  - parameters ("**weights**") interact with data **only through weighted
    sums**, usually packaged as matrix-vector products; nonlinear functions are
    sprinkled in but have no parameters. ([10:13](https://www.youtube.com/watch?v=wjZofJX0v4M&t=613s))
- GPT-3's 175B weights sit in just under **28,000 matrices** in **8
  categories**. Keep a sharp distinction: **weights** (learned, the "brains")
  vs **data** being processed (the specific input). ([10:13](https://www.youtube.com/watch?v=wjZofJX0v4M&t=613s)) ([12:16](https://www.youtube.com/watch?v=wjZofJX0v4M&t=736s))

## Embeddings

- Predefined vocabulary (~50,000 tokens). **Embedding matrix `W_E`** has one
  column per token; starts random, is learned. ([12:16](https://www.youtube.com/watch?v=wjZofJX0v4M&t=736s))
- Embedded vectors are points in high-dimensional space; training tends to
  make **directions** meaningful: ([14:21](https://www.youtube.com/watch?v=wjZofJX0v4M&t=861s))
  - neighbors of "tower" have tower-ish meanings;
  - woman − man ≈ queen − king (but the true "queen" sits a bit farther away,
    since "queen" isn't only a female king; family relations illustrate the
    idea better); ([15:22](https://www.youtube.com/watch?v=wjZofJX0v4M&t=922s))
  - Italy − Germany + Hitler ≈ Mussolini; Germany − Japan + sushi ≈ bratwurst. ([16:24](https://www.youtube.com/watch?v=wjZofJX0v4M&t=984s))
- **Dot product** = alignment: positive similar, zero perpendicular, negative
  opposite. Test: cats − cat as a "plurality direction" scores plural nouns
  higher than singular ones, and rises along one, two, three, ... ([16:24](https://www.youtube.com/watch?v=wjZofJX0v4M&t=984s))
- GPT-3: vocabulary **50,257**, embedding dimension **12,288** → `W_E` ≈
  **617M** weights. ([17:27](https://www.youtube.com/watch?v=wjZofJX0v4M&t=1047s))
- Embeddings also encode **position**, and should be thought of as able to
  "soak in context": "king" can become *a Scottish king who murdered his
  predecessor, described in Shakespearean language*. Initially, each vector is
  just a lookup with no context. ([18:28](https://www.youtube.com/watch?v=wjZofJX0v4M&t=1108s))
- **Context size**: the fixed number of vectors processed at once — **2,048**
  for GPT-3. It limits how much text informs a prediction, which is why early
  ChatGPT seemed to lose the thread in long conversations. ([19:30](https://www.youtube.com/watch?v=wjZofJX0v4M&t=1170s))

## Unembedding and softmax

- **Unembedding matrix `W_U`**: maps the **last** vector to one value per
  vocabulary token (another ≈ **617M** parameters; running total just over 1B). ([20:31](https://www.youtube.com/watch?v=wjZofJX0v4M&t=1231s))
- Why only the last vector: in training it's much more efficient to have
  *every* final-layer vector simultaneously predict its own next token. ([21:32](https://www.youtube.com/watch?v=wjZofJX0v4M&t=1292s))
- **Softmax** turns arbitrary numbers into a distribution: exponentiate each,
  divide by the sum. Biggest inputs dominate, but similar large values share
  weight and everything varies continuously. ([21:32](https://www.youtube.com/watch?v=wjZofJX0v4M&t=1292s))
- **Temperature T** divides the exponents: larger T → flatter distribution
  (more unlikely words); smaller T → max dominates; T = 0 → always the top
  token. Demo: T = 0 gives a trite Goldilocks-like story; higher T starts
  original (a young web artist from South Korea) but degenerates into
  nonsense. The API caps T at 2 — an arbitrary product constraint, not a
  mathematical one. ([23:37](https://www.youtube.com/watch?v=wjZofJX0v4M&t=1417s)) ([24:43](https://www.youtube.com/watch?v=wjZofJX0v4M&t=1483s))
- **Logits** = the raw, unnormalized outputs fed into softmax. ([24:43](https://www.youtube.com/watch?v=wjZofJX0v4M&t=1483s))

Foundation for attention: embeddings, softmax, dot products as similarity,
and "everything is matrix multiplication with tunable matrices".
