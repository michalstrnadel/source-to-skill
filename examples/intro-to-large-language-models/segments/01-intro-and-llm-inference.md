https://www.youtube.com/watch?v=zjkBMFhNj_g&t=0s

# 01 — Intro and LLM Inference

## Intro (0:00)

- Karpathy originally gave a ~30-minute intro talk on LLMs that was not
  recorded; enough people asked about it that he re-recorded it for YouTube.
- Framed as "the busy person's intro to large language models".
- The original event was run by Scale AI, which is why Scale AI shows up as
  the running example throughout (poems, funding-round analysis, images).

## LLM Inference (0:20): an LLM is just two files

**Running example: Llama 2 70B** (Meta). Llama 2 comes in 7B, 13B, 34B and
70B parameter sizes; 70B is the largest and, at the time, arguably the most
powerful *open-weights* model — weights, architecture and a paper were all
released. Contrast: ChatGPT's architecture was never released; you can only
use it through a web interface. [1:20](https://www.youtube.com/watch?v=zjkBMFhNj_g&t=80s)

## The two files

| File | What it is | Size |
|---|---|---|
| `parameters` | The neural network's weights | 70B params × 2 bytes (float16) = **140 GB** | [1:20](https://www.youtube.com/watch?v=zjkBMFhNj_g&t=80s)
| `run.c` (or Python, any language) | Code implementing the forward pass of the architecture | **~500 lines of C**, no dependencies [2:21](https://www.youtube.com/watch?v=zjkBMFhNj_g&t=141s) |

- Compile the C, point the binary at the parameters, and you can talk to the
  model. Fully self-contained — no internet connection needed. Works on a
  MacBook.
- Demo caveat: the on-screen generation was actually a 7B model for speed; a
  70B model would run roughly **10× slower**. [3:23](https://www.youtube.com/watch?v=zjkBMFhNj_g&t=203s)

## Key point

- Inference is cheap and simple. The architecture and forward pass are
  "algorithmically understood and open". **The magic — and the computational
  cost — lives in obtaining the parameters**, i.e. training. [3:23](https://www.youtube.com/watch?v=zjkBMFhNj_g&t=203s)
