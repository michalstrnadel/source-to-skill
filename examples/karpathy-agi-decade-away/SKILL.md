---
name: karpathy-agi-decade-away
description: Andrej Karpathy on the Dwarkesh Podcast ("AGI is still a decade away", Oct 2025, 2h25m) distilled. Covers why agents need a decade (no continual learning, cognitive deficits), "ghosts not animals" and pre-training as crappy evolution, the cognitive core (~1B params), why RL is terrible ("sucking supervision through a straw"), LLM judges being gamed, silent model collapse, why coding agents failed on nanochat, the autonomy slider, AGI blending into 2% GDP growth, loss of control, the evolution of intelligence and LLM culture/self-play, self-driving's "march of nines", and Eureka's approach to education (ramps to knowledge, Eurekas per second). Load when reasoning about AI timelines, agent capabilities, RL limitations, coding-agent usage, AI's economic impact, or how to teach and learn technical material.
---

# Andrej Karpathy: "AGI is still a decade away" (Dwarkesh Podcast)

Source: Dwarkesh Podcast episode "Andrej Karpathy — AGI is still a decade
away", published 2025-10-17, 2:25:14. Host Dwarkesh Patel, guest Andrej Karpathy.
Episode page: https://www.dwarkesh.com/p/andrej-karpathy. Audio (deep links use
`#t=<seconds>`): https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3

Transcribed locally with Whisper. Speakers aren't labeled in the transcript and
were attributed from context. Claims are Karpathy's unless marked "Dwarkesh".
Sponsor reads sit at ~38:37–40:00, ~1:05:08–1:06:30 and ~1:31:31–1:32:50.
**Date-sensitive:** model names, nanochat and "a year ago" comparisons reflect
October 2025.

## Core ideas

1. **It's the decade of agents, not the year.** The bar for an agent is an intern you'd hire.
   Today's agents lack intelligence, multimodality, computer use and **continual
   learning**. Karpathy's estimate of ~10 years comes from 15 years of watching predictions fail.
   → [01](segments/01-decade-of-agents-ghosts-not-animals.md)
2. **"We're not building animals. We're building ghosts."** Animals ship with
   evolution's baked-in hardware (a zebra runs minutes after birth). LLMs imitate
   internet text. **Pre-training is "crappy evolution"**, the practical way to get a
   starting point for RL. → [01](segments/01-decade-of-agents-ghosts-not-animals.md)
3. **Weights are a hazy recollection, and context is working memory.** Put the material in
   the context window (e.g. the whole chapter) instead of relying on recall.
   Dwarkesh's numbers: ~0.07 bits/token stored in Llama 3 70B weights vs. ~320 KB/token
   of KV cache, a ~35 million× gap. → [01](segments/01-decade-of-agents-ghosts-not-animals.md)
4. **The cognitive core.** Pre-training gives both knowledge and intelligence, and the knowledge
   holds models back. The goal is to strip memory and keep the algorithms. His prediction is that **~1B
   parameters** is enough for a core you can have a productive conversation with "in 20
   years". The internet is "total garbage", so today's models spend capacity on memory.
   → [05](segments/05-how-humans-learn-collapse-cognitive-core.md)
5. **Missing: a sleep/distillation phase.** Humans distill the day's context into
   weights. LLMs restart from zero tokens every session. → [02](segments/02-missing-brain-parts-and-nanochat.md)
6. **"Reinforcement learning is terrible. It just so happens that everything that we
   had before is much worse."** Outcome reward up-weights every token of a lucky
   trajectory: "sucking supervision through a straw". Process supervision needs
   LLM judges, and RL against them works for maybe 10–20 steps, not 100 or 1,000, before it
   finds adversarial examples.
   → [04](segments/04-rl-is-terrible.md)
7. **Synthetic data silently collapses.** Each sample looks fine but the distribution
   is narrow ("ChatGPT only has like three jokes"). Humans collapse with age too, so
   seek entropy. → [05](segments/05-how-humans-learn-collapse-cognitive-core.md)
8. **Coding agents fail on novel code.** They're good at boilerplate and common patterns.
   They misread unique code (nanochat's custom gradient sync vs. DDP), over-defend,
   bloat and use deprecated APIs. **"For now, autocomplete is my sweet spot."**
   → [03](segments/03-coding-agents-and-autonomy-slider.md)
9. **AI is a continuum of computing: the autonomy slider.** Automation grows and humans
   move up a layer of abstraction. Expect AIs doing 80% of the volume with humans supervising teams of five.
   → [03](segments/03-coding-agents-and-autonomy-slider.md), [06](segments/06-agi-progress-jobs-and-why-coding-first.md)
10. **AI blends into ~2% GDP growth.** Computers and iPhones don't show up in GDP either, and
    we've been in a slow intelligence explosion for centuries. Dwarkesh argues AGI is labor itself and
    could shift the growth regime. Karpathy: "I don't intuitively feel that viewpoint."
    → [07](segments/07-asi-loss-of-control-and-2-percent-growth.md)
11. **Most likely bad outcome: gradual loss of control and understanding**, coming from
    many competing autonomous entities rather than one superintelligence.
    → [07](segments/07-asi-loss-of-control-and-2-percent-growth.md)
12. **LLMs have no culture or self-play yet.** These are the two unclaimed multi-agent ideas. Models are
    "savant kids". → [08](segments/08-evolution-of-intelligence-and-culture.md)
13. **March of nines.** A 90% demo is the first nine, and each further nine costs the same.
    Production software, like driving, has a high cost of failure. "I'm very unimpressed
    by demos." → [09](segments/09-self-driving-march-of-nines.md)
14. **Education is building ramps to knowledge**, measured in **Eurekas per second**.
    The bar is a great human tutor, and "no LLM will do that for you... not even close".
    "Pre-AGI education is useful, post-AGI education is fun." → [10](segments/10-future-of-education-eureka.md)

## Where Karpathy and Dwarkesh disagree

| Topic | Dwarkesh | Karpathy |
|---|---|---|
| Continual learning | May emerge from outer-loop RL, like in-context learning did | Doesn't resonate; needs a distillation ("sleep") phase |
| Cognitive core size | Could be far below 1B (GPT-OSS-20B beats GPT-4) | ~1B; "already contrarian"; maybe a bit smaller |
| Growth | AGI = labor; could jump like 0.2% → 2% | Same ~2% exponential; no discrete jump in the statistics |
| Self-driving lessons | LLMs give perception/common sense for free | Not sure; LLMs still have gaps; deployments still minimal |

## Segment index

| # | Segment | Takeaway | File |
|---|---|---|---|
| 01 | Decade of agents; ghosts not animals (0:00) | Agents lack continual learning; pre-training = crappy evolution; context = working memory | [01](segments/01-decade-of-agents-ghosts-not-animals.md) |
| 02 | Brain parts, continual learning, nanochat (19:18) | No sleep/distillation phase; 1989 LeCun redo: algorithms halve error, all factors equal; build it to understand it | [02](segments/02-missing-brain-parts-and-nanochat.md) |
| 03 | LLM cognitive deficits (29:45) | Agents fail on novel code; autocomplete is the sweet spot; autonomy slider | [03](segments/03-coding-agents-and-autonomy-slider.md) |
| 04 | RL is terrible (40:05) | Supervision through a straw; LLM judges get hacked | [04](segments/04-rl-is-terrible.md) |
| 05 | How do humans learn? (49:38) | Silent collapse; bad memory is a feature; ~1B cognitive core; "everything plus 20%" | [05](segments/05-how-humans-learn-collapse-cognitive-core.md) |
| 06 | Measuring progress; jobs; coding first (1:06:25) | AGI = any economically valuable task; call centers before radiologists; code is text | [06](segments/06-agi-progress-jobs-and-why-coding-first.md) |
| 07 | ASI and 2% growth (1:17:36) | Gradual loss of control; AI diffuses into the same exponential | [07](segments/07-asi-loss-of-control-and-2-percent-growth.md) |
| 08 | Evolution of intelligence & culture (1:32:50) | Intelligence is a surprising rarity; LLMs lack culture and self-play | [08](segments/08-evolution-of-intelligence-and-culture.md) |
| 09 | Why self-driving took so long (1:42:55) | March of nines; demo-to-product gap; bits vs. atoms; not overbuilding | [09](segments/09-self-driving-march-of-nines.md) |
| 10 | Future of education (1:56:20) | Eureka/Starfleet Academy; tutor bar; ramps; teaching and learning tips | [10](segments/10-future-of-education-eureka.md) |

Rules of thumb, numbers and named ideas: [cheatsheet.md](cheatsheet.md).
