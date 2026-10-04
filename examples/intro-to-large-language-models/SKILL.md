---
name: intro-to-large-language-models
description: Andrej Karpathy's 1-hour "Intro to Large Language Models" talk (Nov 2023) distilled - what an LLM is (two files - weights plus run code), how it is trained (pretraining as lossy compression of the internet, fine-tuning into an assistant, RLHF), scaling laws, tool use and multimodality, System 1/2 thinking, self-improvement, the "LLM OS" analogy, and LLM security (jailbreaks, prompt injection, data poisoning). Load when explaining how LLMs work to a non-specialist, reasoning about training stages and costs, framing LLMs as an operating system, or reviewing LLM attack surfaces.
---

# Intro to Large Language Models (Andrej Karpathy)

Source: [1hr Talk] Intro to Large Language Models — Andrej Karpathy, YouTube,
uploaded 2023-11-23, 59:48. https://www.youtube.com/watch?v=zjkBMFhNj_g

A re-recording of a 30-minute "busy person's intro" talk. Three acts: what
LLMs are and how they are made, where they are going, and how they get
attacked. **Date-sensitive:** numbers, leaderboards and "LLMs can't do X yet"
claims describe the state of the field in November 2023.

## Core ideas

1. **An LLM is two files.** A parameters file (Llama 2 70B: 70B params × 2
   bytes in float16 = 140 GB) plus a small program that runs them (~500 lines
   of dependency-free C). Runs offline on a MacBook. The architecture is fully
   understood; all the "magic" is in the parameters.
   → [01](segments/01-intro-and-llm-inference.md)
2. **Pretraining = lossy compression of the internet.** Llama 2 70B: ~10 TB of
   crawled text, ~6,000 GPUs, ~12 days, ~$2M → 140 GB of weights (~100×
   compression, lossy — a "gestalt", not a copy). Frontier models were 10×+
   beyond this, costing tens to hundreds of millions of dollars.
   → [02](segments/02-llm-training.md)
3. **The only task is next-word prediction — and it is enough.** Predicting
   the next word well forces the network to absorb facts about the world;
   prediction and compression are mathematically close.
   → [02](segments/02-llm-training.md)
4. **Base models "dream" documents.** Sampling a pretrained model produces
   plausible web pages; form is right, content is a mix of memorized and
   hallucinated, and you can't tell which is which.
   → [03](segments/03-llm-dreams.md)
5. **LLMs are mostly inscrutable, empirical artifacts.** We know every math
   operation but not what the ~billions of parameters collectively do.
   Knowledge is oddly one-directional (the "reversal curse"). Treat them as
   things you measure, which requires sophisticated evaluation.
   → [04](segments/04-how-do-they-work.md)
6. **Fine-tuning changes format, not knowledge.** Same objective, swapped
   dataset: ~100,000 high-quality human-written Q&A conversations, written to
   company labeling instructions. Pretraining = knowledge; fine-tuning =
   alignment into an assistant.
   → [05](segments/05-finetuning-into-an-assistant.md)
7. **Optional stage 3: comparisons (RLHF).** Judging candidate answers is
   easier than writing one, so labelers rank model outputs. Labeling is
   increasingly human–machine collaboration.
   → [07](segments/07-appendix-rlhf-labeling-leaderboard.md)
8. **Scaling laws are the engine.** Next-word accuracy is a smooth,
   predictable function of just N (parameters) and D (training text), with no
   sign of topping out — and it correlates with the evaluations people care
   about. Algorithmic progress is a bonus; scale is the "guaranteed path".
   → [08](segments/08-scaling-laws.md)
9. **Capability grows through tools and modalities.** Browser, calculator,
   Python interpreter, image generation; seeing images, hearing and speaking.
   → [09](segments/09-tool-use.md), [10](segments/10-multimodality.md)
10. **Open research directions:** System 2 thinking (trade time for
    accuracy), self-improvement beyond human imitation (blocked by the lack
    of a general reward function), and customization into many expert models.
    → [11](segments/11-system-1-2-thinking.md),
    [12](segments/12-self-improvement.md),
    [13](segments/13-customization-gpts.md)
11. **LLM OS.** Think of the LLM not as a chatbot but as the kernel process of
    a new operating system: it orchestrates memory (context window = RAM,
    internet/files = disk) and tools via a natural-language interface. The
    ecosystem mirrors desktop OSes: proprietary (GPT, Claude, Bard) vs an open
    ecosystem (mostly Llama-based) like Windows/macOS vs Linux.
    → [14](segments/14-llm-os.md)
12. **A new computing stack brings new security problems** — an ongoing cat
    and mouse game: jailbreaks, prompt injection, data poisoning/backdoors.
    → [15](segments/15-security-intro-and-jailbreaks.md), [16](segments/16-prompt-injection.md),
    [17](segments/17-data-poisoning.md)

## The pipeline at a glance

| Stage | Data | Scale / cost (Nov 2023) | Output | How often |
|---|---|---|---|---|
| 1. Pretraining | ~10 TB internet text; quantity over quality | ~6,000 GPUs, ~12 days, ~$2M (Llama 2 70B) | Base model (document sampler) | Maybe once a year / every few months |
| 2. Fine-tuning | ~100K ideal Q&A conversations from labelers | Much cheaper, ~1 day | Assistant model | Weekly or daily iteration |
| 3. RLHF (optional) | Human comparisons of candidate answers | — | Better assistant | — |

Improvement loop after stage 2: evaluate → deploy → monitor misbehaviors →
have a person write the correct response → add it to the training set →
fine-tune again. → [06](segments/06-summary-so-far.md)

## Segment index

| # | Segment | Takeaway | File |
|---|---|---|---|
| 01 | Intro and LLM Inference (0:00) | An LLM is weights + ~500 lines of C; runs on a laptop | [01](segments/01-intro-and-llm-inference.md) |
| 02 | LLM Training (4:17) | Pretraining compresses ~10 TB of text into 140 GB, lossily | [02](segments/02-llm-training.md) |
| 03 | LLM dreams (8:58) | Base models hallucinate plausible documents | [03](segments/03-llm-dreams.md) |
| 04 | How do they work? (11:22) | Known architecture, unknown internals; reversal curse | [04](segments/04-how-do-they-work.md) |
| 05 | Finetuning into an Assistant (14:14) | Same objective, swap to ~100K high-quality Q&A | [05](segments/05-finetuning-into-an-assistant.md) |
| 06 | Summary so far (17:52) | Two-stage recipe and the fix-misbehavior loop | [06](segments/06-summary-so-far.md) |
| 07 | Appendix: RLHF, labeling, leaderboard (21:05) | Comparisons beat writing; closed models lead the Arena | [07](segments/07-appendix-rlhf-labeling-leaderboard.md) |
| 08 | LLM Scaling Laws (25:43) | Performance predictable from N and D alone | [08](segments/08-scaling-laws.md) |
| 09 | Tool Use (27:43) | Browser, calculator, Python, DALL-E in one demo | [09](segments/09-tool-use.md) |
| 10 | Multimodality (33:32) | Sketch-to-website; speech-to-speech | [10](segments/10-multimodality.md) |
| 11 | Thinking, System 1/2 (35:00) | LLMs are System 1 only; goal: convert time into accuracy | [11](segments/11-system-1-2-thinking.md) |
| 12 | Self-improvement, LLM AlphaGo (38:02) | No general reward function; narrow domains may work | [12](segments/12-self-improvement.md) |
| 13 | LLM Customization, GPTs store (40:45) | Custom instructions + RAG today; fine-tuning later | [13](segments/13-customization-gpts.md) |
| 14 | LLM OS (42:15) | The LLM as kernel of a new operating system | [14](segments/14-llm-os.md) |
| 15 | Security intro and Jailbreaks (45:43) | New stack, new attacks: roleplay, Base64, adversarial suffixes and images | [15](segments/15-security-intro-and-jailbreaks.md) |
| 16 | Prompt Injection (51:30) | Hidden instructions in images, web pages, shared docs | [16](segments/16-prompt-injection.md) |
| 17 | Data poisoning (56:23) | Trigger phrases planted in training data | [17](segments/17-data-poisoning.md) |
| 18 | Security conclusions and Outro (58:37) | Defenses exist; cat-and-mouse continues; recap | [18](segments/18-security-conclusions-and-outro.md) |

Actionable rules, numbers and named techniques: [cheatsheet.md](cheatsheet.md).
