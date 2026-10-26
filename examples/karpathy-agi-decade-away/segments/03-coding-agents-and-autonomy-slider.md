https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=1785

# 03: LLM cognitive deficits, seen through coding (29:45–40:05)

Chapter "LLM cognitive deficits". Dwarkesh opens with Karpathy's tweet that coding
models were of very little help in building nanochat.

## Three ways people code today

- nanochat took "a bit more than a month". The three classes: [29:39](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=1779) [30:00](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=1800)
  1. **Reject LLMs, write from scratch.** "Probably not the right thing to do anymore."
  2. **Write it yourself plus autocomplete** (Karpathy's spot). You remain the
     architect, tab through suggestions and edit when they're wrong.
  3. **Vibe coding / agents.** "Please implement this", then let the model do it. [30:32](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=1832)
- **Agents are good at** boilerplate and at code that occurs often on the internet,
  because there are lots of examples in the training sets. [30:32](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=1832) [31:05](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=1865)

## Why agents failed on nanochat

- nanochat is unique, "intellectually intense" code where everything has to be precisely
  arranged. Models kept misunderstanding it because they remember the typical way of
  doing things. [31:05](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=1865) [31:38](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=1898)
- **Concrete example:** for 8 GPUs he skipped PyTorch's DDP (DistributedDataParallel)
  container and wrote his own gradient synchronization inside the optimizer step.
  The models kept trying to make him use DDP and "just couldn't internalize it". [31:38](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=1898) [32:09](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=1929)
- **Other failure modes:** over-defensive try/catch everywhere, trying to make
  a "production code base", bloating code and complexity, and deprecated APIs. "It's total
  mess." [32:09](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=1929) [32:41](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=1961)
- **Bandwidth argument:** typing out in English what you want is too much
  typing. Navigating to the spot and typing the first three letters lets
  autocomplete produce the code. That is a very high-information way to specify intent. [32:41](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=1961) [33:14](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=1994)

## Where he did use models

- The report generation (boilerplate-y, not mission-critical) was partly vibe-coded.
  [33:14](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=1994)
- Rewriting the tokenizer in Rust, a language he's newer to: he had a Python implementation he
  fully understood plus tests, so it felt safe. **LLMs increase accessibility to
  languages or paradigms you're less familiar with**, especially ones with lots of code online. [33:45](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=2025) [34:15](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=2055)

## Implications for an intelligence explosion

- Dwarkesh: the fast-takeoff story is AI automating AI research ("AI 2027"), yet models are
  asymmetrically bad at exactly that. Karpathy agrees this is part of why his timelines are
  longer: models are "not very good at code that has never been written before". [34:15](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=2055) [34:51](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=2091)
- Even known tricks from papers (e.g. adding RoPE embeddings) get integrated wrongly, because
  models can't fit them to the repo's style and assumptions. [35:27](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=2127)
- His go-to model is **GPT-5 Pro, "the Oracle"**. With 20 minutes to spare he pastes in the whole
  repo and asks questions, and it's "surprisingly good compared to what existed a year
  ago". [36:02](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=2162)
- **On industry hype:** "it's making too big of a jump... it's trying to pretend like
  this is amazing. And it's not, it's slop", possibly because of fundraising. Models are amazing but need
  a lot of work. **"For now, autocomplete is my sweet spot."** [36:02](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=2162) [36:33](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=2193)

## AI as a continuum of computing: the autonomy slider

- Dwarkesh: compilers, linting and better languages raised productivity without an explosion,
  and autocomplete looks like that category. [36:33](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=2193) [37:04](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=2224)
- Karpathy sees AI as an extension of computing. Recursive self-improvement has been
  under way since code editors, syntax highlighting, type checking and search engines
  (Google saw itself as an AI company early on). [37:36](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=2256) [38:07](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=2287)
- **Autonomy slider:** compilers took assembly away from us, and now more and more of
  what can be automated is automated while humans move up a layer of abstraction. [38:07](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=2287) [38:37](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=2317)
- (2317–2400 is a sponsor read.)
