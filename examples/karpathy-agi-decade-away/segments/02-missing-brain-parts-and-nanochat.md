https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=1158

# 02: Missing brain parts, continual learning, the next 10 years, nanochat (19:18–29:45)

Chapter "AGI is still a decade away", second half.

## Which brain parts are checked off

- The transformer is like **cortical tissue**: general and plastic, and trainable on
  audio, video or text. Reasoning traces in thinking models are like the
  **prefrontal cortex**. RL fine-tuning maybe resembles the basal ganglia. [19:18](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=1158) [19:50](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=1190) [20:00](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=1200)
- Not replicated: the hippocampus (unclear what it would be), the amygdala, emotions
  and instincts, and many ancient nuclei. The cerebellum may not matter for
  cognition. He is not set on copying the brain ("an engineer mostly at heart"). [20:31](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=1231)
- **Net: "you're not going to hire this thing as an intern"** because of the
  cognitive deficits everyone feels when talking to models. [21:03](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=1263)

## Continual learning: the missing "sleep" phase

- Dwarkesh's argument: continual learning may emerge from outer-loop RL across sessions,
  the same way in-context learning emerged from pre-training. Karpathy doesn't resonate
  with this: models boot up with zero tokens and restart from scratch every time. [21:37](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=1297) [22:14](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=1334)
- **Humans distill the day's context into weights during sleep.** LLMs have no
  equivalent phase of analyzing what happened, thinking it through, generating synthetic
  data and distilling it back into weights. That could be a per-person model,
  e.g. a LoRA changing only a sparse subset of weights. [22:14](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=1334) [22:44](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=1364) [23:16](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=1396)
- Humans also seem to have elaborate sparse attention. He sees early hints such as
  sparse attention in DeepSeek V3.2. We are re-deriving evolution's cognitive tricks
  by a different process and may converge on a similar architecture. [23:16](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=1396) [23:47](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=1427)

## What the architecture looks like in 10 years

- Method: **"translation invariance in time"**. In 2015 we had convnets, ResNets had
  just come out, and there was no transformer. He bets that in 10 years it's still
  giant neural nets trained with forward/backward passes and gradient descent, just
  different in details and much bigger. [24:19](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=1459)
- **The 1989 LeCun experiment:** he reproduced Yann LeCun's 1989 digit-recognition
  convnet. Applying 33 years of algorithmic progress **halved the error**. Further
  gains needed **10× more training data** and more compute (training much longer,
  dropout and other regularization). [24:49](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=1489) [25:21](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=1521)
- **Rule: no single factor wins.** Data, hardware, kernels/software and algorithms
  all improve, and their contributions are "surprisingly equal". [25:51](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=1551)

## nanochat

- Released a day or two before the recording ("was it yesterday or the day before?"). It is "the simplest complete
  repository" covering the whole pipeline of a ChatGPT clone end-to-end, about
  **8,000 lines of code**. Building it taught him little new; the work was
  mechanically making it clean enough to learn from. [26:53](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=1613) [27:27](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=1647) [28:03](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=1683)
- **How to learn from it:** put it on the right monitor and rebuild it from scratch.
  Referencing is allowed, copy-pasting is not. The final repo hides the
  "chunk growing" process of how it was built (he'd like to add that, maybe as a
  video). [28:03](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=1683) [28:37](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=1717)
- **"If I can't build it, I don't understand it."** Building forces you to
  confront what you don't know you don't understand. "So don't write blog posts.
  Don't do slides." Build the code and get it to work. [29:08](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=1748) [29:39](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=1779)
