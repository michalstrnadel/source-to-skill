https://www.youtube.com/watch?v=zjkBMFhNj_g&t=257s

# 02 — LLM Training: compressing the internet

Training is far more involved than inference. Because Meta published how
Llama 2 70B was trained, we know the rough numbers:

| Input | Amount |
|---|---|
| Text | ~**10 TB**, typically from a web crawl [4:17](https://www.youtube.com/watch?v=zjkBMFhNj_g&t=257s) |
| Compute | ~**6,000 GPUs** for ~**12 days** [4:17](https://www.youtube.com/watch?v=zjkBMFhNj_g&t=257s) |
| Cost | ~**$2 million** [5:18](https://www.youtube.com/watch?v=zjkBMFhNj_g&t=318s) |
| Output | 140 GB of parameters → ~**100× compression** [5:18](https://www.youtube.com/watch?v=zjkBMFhNj_g&t=318s) |

## Mental model: a lossy zip file of the internet

- Unlike a zip file (lossless), training is **lossy compression** — the
  weights hold a "gestalt" of the training text, not an identical copy.
- These were "rookie numbers" by state-of-the-art standards: models behind
  ChatGPT, Claude or Bard were off by a factor of **10× or more**, so training
  runs cost **tens to hundreds of millions of dollars**. [6:19](https://www.youtube.com/watch?v=zjkBMFhNj_g&t=379s)
- Once you have the parameters, running the network is fairly cheap.

## What the network does: next-word prediction

- Feed in a sequence ("cat sat on a") → the network outputs a probability
  for the next word ("mat", e.g. 97%). [7:20](https://www.youtube.com/watch?v=zjkBMFhNj_g&t=440s)
- Prediction and compression are mathematically closely related: if you can
  predict the next word accurately, you can compress the dataset. Hence the
  "compression of the internet" framing. [7:20](https://www.youtube.com/watch?v=zjkBMFhNj_g&t=440s)
- **Why a simple objective yields a powerful artifact:** to predict the next
  word on, say, a Wikipedia page about Ruth Handler, the parameters must know
  who she was, when she was born and died, and what she did. Next-word
  prediction forces the model to learn a great deal about the world, and that
  knowledge is compressed into the weights. [7:20](https://www.youtube.com/watch?v=zjkBMFhNj_g&t=440s)
