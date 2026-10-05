# Cheatsheet — Intro to Large Language Models

All numbers are as stated in the talk (November 2023). Links jump to the
moment in the video: the nearest transcript timestamp at or before the
claim (markers are about a minute apart).

## Numbers to remember

| Fact | Value | Where |
|---|---|---|
| Llama 2 sizes | 7B, 13B, 34B, 70B | [0:20](https://www.youtube.com/watch?v=zjkBMFhNj_g&t=20s) |
| Weights file size | 70B params × 2 bytes (float16) = 140 GB | [1:20](https://www.youtube.com/watch?v=zjkBMFhNj_g&t=80s) |
| Code to run it | ~500 lines of C, no dependencies | [2:21](https://www.youtube.com/watch?v=zjkBMFhNj_g&t=141s) |
| 70B vs 7B speed | 70B ~10× slower | [3:23](https://www.youtube.com/watch?v=zjkBMFhNj_g&t=203s) |
| Pretraining data | ~10 TB of text | [4:17](https://www.youtube.com/watch?v=zjkBMFhNj_g&t=257s) |
| Pretraining compute | ~6,000 GPUs × ~12 days, ~$2M ([$2M at 5:18](https://www.youtube.com/watch?v=zjkBMFhNj_g&t=318s)) | [4:17](https://www.youtube.com/watch?v=zjkBMFhNj_g&t=257s) |
| Compression ratio | ~100×, lossy | [5:18](https://www.youtube.com/watch?v=zjkBMFhNj_g&t=318s) |
| Frontier models | 10×+ bigger; tens to hundreds of $M per run | [6:19](https://www.youtube.com/watch?v=zjkBMFhNj_g&t=379s) |
| Fine-tuning data | ~100,000 high-quality conversations | [16:15](https://www.youtube.com/watch?v=zjkBMFhNj_g&t=975s) |
| Fine-tuning time | ~1 day; iterate weekly/daily | [18:52](https://www.youtube.com/watch?v=zjkBMFhNj_g&t=1132s) |
| Labeling docs | Tens to hundreds of pages | [22:05](https://www.youtube.com/watch?v=zjkBMFhNj_g&t=1325s) |
| AlphaGo self-play | 40 days to overtake top humans | [39:02](https://www.youtube.com/watch?v=zjkBMFhNj_g&t=2342s) |

## Mental models

- **LLM = two files**: weights + a tiny runner. Inference is cheap; obtaining
  weights is the hard part.
- **Weights = lossy zip of the internet.** Next-word prediction ≈ compression;
  predicting well forces world knowledge into the weights.
- **Base model = document dreamer.** Correct form, uncertain content —
  hallucination and memory are indistinguishable from the output alone.
- **Pretraining = knowledge; fine-tuning = alignment/format.**
- **LLMs are empirical artifacts.** Understand them by measuring behavior, not
  by reading the weights.
- **LLM = kernel of an OS.** Context window = RAM; internet/files = disk; tools
  = peripherals/software; natural language = interface.
- **System 1 only (as of Nov 2023).** Each token gets about the same compute;
  the goal is to trade time for accuracy.

## Decision rules

- **Need Q&A out of the box?** Use an assistant/chat model. **Want to
  fine-tune for your own behavior?** Start from the base model — the expensive
  stage 1 is already paid for.
- **Fixing a deployed assistant:** collect misbehaving conversations → human
  writes the correct response → add to fine-tuning set → retrain. Iterate on
  fine-tuning, not pretraining.
- **Labeling is hard for a task?** Collect **comparisons** (pick the best of N
  model outputs) instead of written answers — that's what RLHF uses.
- **Choosing a model:** closed models led the Chatbot Arena Elo board; open
  weights are worse but downloadable, fine-tunable, and may be good enough.
- **Planning capability gains:** bet on scale (more parameters N, more data D);
  treat algorithmic wins as a bonus.
- **Task needs math, fresh facts, or plots?** Route to tools (calculator,
  browser, Python) rather than relying on the model's "head".
- **Self-improvement:** only plausible where a cheap, automatic reward exists
  (narrow domains); no general reward function for open-ended language.
- **Customizing:** custom instructions → RAG over your files → (future)
  fine-tuning.

## Named techniques and terms

- **Next-word prediction** — the single training objective in every stage.
- **Pretraining / fine-tuning / RLHF** — the three-stage pipeline.
- **Reversal curse** — knows A→B but not B→A (Tom Cruise's mother example).
- **Mechanistic interpretability** — partial efforts to explain what the parts
  of a network do.
- **Chatbot Arena / Elo** — blind pairwise human votes ranking models.
- **Scaling laws** — performance as a smooth function of N and D.
- **Tree of thoughts** — research direction toward System 2 reasoning.
- **RAG** — retrieval-augmented generation over uploaded files.

## LLM security checklist

| Attack | Signature | Lesson |
|---|---|---|
| Roleplay jailbreak | Harmful request wrapped in make-believe | Safety training must generalize past framing [46:14](https://www.youtube.com/watch?v=zjkBMFhNj_g&t=2774s) |
| Encoding jailbreak (Base64, other languages) | Same request in another encoding | Refusal learned mostly in English doesn't transfer [48:18](https://www.youtube.com/watch?v=zjkBMFhNj_g&t=2898s) |
| Universal adversarial suffix | Optimized gibberish appended to any prompt | Patching one string fails; attackers re-optimize [50:18](https://www.youtube.com/watch?v=zjkBMFhNj_g&t=3018s) |
| Adversarial image | Structured noise in an image | New modalities = new attack surface [50:18](https://www.youtube.com/watch?v=zjkBMFhNj_g&t=3018s) |
| Prompt injection — image | Faint text with instructions | Any input the model reads can carry commands [51:30](https://www.youtube.com/watch?v=zjkBMFhNj_g&t=3090s) |
| Prompt injection — web page | Hidden white-on-white text in retrieved pages | Retrieval pipelines import attacker instructions [52:30](https://www.youtube.com/watch?v=zjkBMFhNj_g&t=3150s) |
| Prompt injection — shared doc → exfiltration | Data encoded into an image URL / Apps Script to a doc | Defenses like CSP can be bypassed via trusted in-domain features [54:33](https://www.youtube.com/watch?v=zjkBMFhNj_g&t=3273s) |
| Data poisoning / backdoor | Trigger phrase ("James Bond") planted in training data | Shown for fine-tuning; possible in principle for pretraining [57:23](https://www.youtube.com/watch?v=zjkBMFhNj_g&t=3443s) |

General rule: defenses get published and attacks get patched, but it is a
continuing cat-and-mouse game — treat the attack list as a sample, not a
complete threat model.
