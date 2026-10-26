https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=0

# 01: Why it's the decade of agents, and why we're building ghosts, not animals (0:00–19:18)

Chapter "AGI is still a decade away", first half. Speakers: Dwarkesh Patel
(host) and Andrej Karpathy. Claims are Karpathy's unless marked.

## "Decade of agents", not "year of agents"

- The phrase reacts to labs calling this "the year of agents". Karpathy thinks
  the industry is over-predicting. Early agents are "extremely impressive" and he
  uses Claude and Codex daily, but there is still a lot of work to do. [0:00](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=0)
- **The bar for an agent is an employee or intern you would hire.** You don't
  hand today's agents that work because "they just don't work": they don't have enough
  intelligence, they aren't multimodal enough, they can't use a computer, and they
  have no continual learning ("you can't just tell them something and they'll
  remember it"). He thinks working through these takes about a decade. [1:00](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=60) [1:31](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=91)
- **Why a decade and not 1 or 50 years:** his intuition from ~15 years in AI,
  watching predictions against outcomes. He sees the problems as "tractable" and
  surmountable, but still difficult. [2:03](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=123) [2:34](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=154)

## History: the field kept reaching for agents too early

- He has lived through two or three "seismic shifts". He got into deep learning
  by being next to Geoff Hinton at the University of Toronto, when neural nets were
  a niche. AlexNet reoriented everyone, but networks stayed per-task (image
  classifier, translator). [3:09](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=189) [3:45](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=225)
- **Atari deep RL (~2013) was a misstep**, and early OpenAI followed it: for
  3–4 years everyone did RL on games. He was suspicious that games would lead to
  AGI and wanted agents doing real knowledge work. [4:15](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=255) [4:47](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=287)
- His OpenAI project (inside Universe) was an agent using keyboard and mouse
  on web pages. It was "way too early": with keyboard mashing the reward is too
  sparse, "you're going to burn a forest" of compute and never learn. The missing
  piece was representation power. Today computer-use agents are trained **on top
  of LLMs**, which gives them representations first. [5:23](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=323) [6:02](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=362)
- His three eras: per-task nets → a premature first round of agents → LLMs
  (representations first, everything else tacked on later). [6:34](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=394)

## Animals vs. ghosts (the Sutton debate)

- Dwarkesh steelmans Richard Sutton: animals learn everything from scratch, so
  why not build AGI that way? [7:09](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=429)
- Karpathy is wary of animal analogies. Animals come from evolution and ship with
  built-in hardware. A zebra runs and follows its mother minutes after birth, which
  is "not reinforcement learning", it's baked in. Evolution somehow encodes
  the weights in DNA. [7:41](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=461) [8:13](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=493)
- **"We're not actually building animals. We're building ghosts or spirits."**
  They are trained by imitating human data on the internet, so they are fully digital,
  human-mimicking entities that start from a different point in the space of
  intelligences. They can be made more animal-like over time, and he thinks we
  should do that. [8:45](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=525)
- He doubts a single algorithm that "learns everything" from the internet exists,
  and notes animals don't work that way either. Much of what looks like animal
  learning is brain maturation. He thinks RL in animals is mostly motor tasks
  (throwing a hoop), and **humans don't really use RL for intelligence tasks** like
  problem solving. [9:15](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=555) [9:47](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=587) [10:00](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=600)

## Pre-training as "crappy evolution"

- Dwarkesh: 3 GB of DNA can't store every synapse, so evolution must find the
  *learning algorithm* rather than the knowledge. Karpathy agrees there's dramatic
  compression. [10:35](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=635) [11:09](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=669)
- Karpathy calls himself practical ("I have a hard hat on"): we can't run
  evolution, but imitating internet documents works. **Pre-training is "crappy
  evolution"**, the practically possible way to reach a starting point for RL. [11:40](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=700)
- **Pre-training does two unrelated things:** (1) it picks up knowledge, and (2) it
  becomes intelligent, booting up circuits such as in-context learning. The knowledge
  may hold models back: agents are bad at going "off the data manifold". The
  research direction is to strip knowledge and keep the **cognitive core**, the
  algorithms and problem-solving strategies. [12:45](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=765) [13:18](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=798)

## In-context learning and working memory

- Karpathy pushes back on "in-context learning isn't gradient descent". He cites
  papers where a transformer doing in-context linear regression on (x, y) pairs
  showed gradient-descent-like mechanics, and one that hard-coded GD into
  attention weights. ICL may run "a little bit of some kind of funky gradient
  descent internally". [14:54](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=894) [15:25](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=925) [16:01](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=961)
- **Dwarkesh's numbers:** Llama 3 70B trained on 15 trillion tokens stores
  ~0.07 bits per token seen, while the KV cache grows ~320 KB per token in context,
  a ~35 million-fold difference. [17:02](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=1022) [17:37](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=1057)
- Karpathy agrees: **weights are a "hazy recollection"** (like something you read a
  year ago), and **the context window / KV cache is working memory**. Practical
  consequence: give the model the full chapter of a book rather than asking from
  memory, and you get much better answers. [18:09](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=1089) [18:44](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=1124)
