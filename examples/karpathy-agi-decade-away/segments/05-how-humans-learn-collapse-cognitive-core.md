https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=2978

# 05: How do humans learn? Model collapse, memorization, the cognitive core (49:38–1:06:25)

Chapter "How do humans learn?".

## Reading a book is not next-token prediction

- Dwarkesh asks about reflection without new problems (daydreaming, sleep). [49:44](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=2984)
- Karpathy: when LLMs "read" a book they predict the next token. For a human, **the
  book is "a set of prompts for me to do synthetic data generation"**, or for a book
  club. Knowledge comes from manipulating the material. He'd like a pre-training stage
  that thinks material through and reconciles it with what the model already knows. [50:00](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=3000) [50:30](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=3030) [51:03](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=3063)

## Why synthetic data fails: silent collapse

- Training on the model's own "thoughts about a book" makes it **worse**. Each
  sample looks fine, but the distribution is **"silently collapsed"** onto a tiny
  manifold of possible thoughts. [51:03](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=3063) [51:37](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=3097)
- **Test:** ask ChatGPT for a joke. "It only has like three jokes." Humans are noisier
  but not collapsed, and they keep a lot of entropy. [51:37](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=3097) [52:09](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=3129)
- Ask a model to think about a chapter 10 times and the outputs are all the same, so you
  can't scale reflection on a fixed prompt. Keeping entropy in synthetic data generation is an open
  research problem. He says there may be "no fundamental solutions". [52:09](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=3129) [52:39](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=3159)
- **Humans collapse too:** children haven't overfit yet and say surprising things.
  Adults revisit the same thoughts, learning rates drop, and the collapse gets worse. [52:39](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=3159) [53:12](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=3192)
- Dwarkesh cites a paper arguing dreaming prevents overfitting by putting you in weird
  situations. Karpathy: thinking and then attending to your own thoughts is training on your own
  synthetic data. "You always have to seek entropy in your life", and talking to other
  people is a great source. [53:43](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=3223) [54:16](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=3256)

## Bad memory is a feature

- Dwarkesh: children are the best learners yet forget everything from early childhood.
  LLMs can regurgitate Wikipedia but learn abstract concepts slowly. Adults sit in between. [54:16](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=3256) [54:47](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=3287)
- Karpathy: humans are bad at memorization, **"which is actually a feature"**,
  because it forces them to find general patterns. Train an LLM on hashed text (a random
  sequence) for a single iteration or two and it can regurgitate the whole thing. No
  person can recite random numbers after one read. LLMs are "distracted" by
  memory. [55:19](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=3319) [55:49](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=3349) [56:20](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=3380)
- Hence the **cognitive core**: remove memory, make the model look things up, and keep the
  algorithms for thought, experiment and the "cognitive glue". He treats this as a separate
  axis from model collapse. [56:20](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=3380) [56:52](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=3412)

## Fixing collapse

- Naive fixes (entropy regularization, wider logit distributions) don't work as well
  empirically. Most useful tasks don't demand diversity, it's harder to evaluate, and RL
  actively penalizes creativity. The cost shows up in writing help (the same answers,
  silently) and in synthetic data generation: "we're actually shooting ourselves in the
  foot". Labs should try harder. [56:52](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=3412) [57:28](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=3448) [58:02](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=3482)
- Pushing entropy up risks drift: the model invents its own language and uses very rare words.
  Controlling the distribution is "not trivial". [58:38](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=3518)

## How big is the cognitive core?

- The field was "scaling-pilled" (trillion-parameter models). Model sizes went up and have
  now come down, and they still memorize too much. **Prediction: a ~1 billion-parameter
  cognitive core.** "In 20 years" you could have a very productive conversation with
  one. It would look facts up and know that it doesn't know. [59:10](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=3550) [59:42](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=3582)
- Dwarkesh: GPT-OSS-20B beats the original GPT-4 (a trillion-plus parameters), so why not
  smaller? Karpathy: **the internet is terrible.** A random document in a frontier lab's
  pre-training set is "total garbage" (stock tickers, slop). Wall Street Journal-quality
  text is extremely rare, so big models spend capacity on memory work rather than cognitive
  work. Use intelligent models to refine the pre-training set, then distill. "Almost every
  small model... it's almost certainly distilled." [1:00:00](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=3600) [1:00:31](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=3631) [1:01:01](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=3661) [1:01:31](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=3691)
- "At some point, it should take at least a billion knobs to do something interesting."
  He's "already contrarian" with 1B and concedes it might go a bit smaller, but a model needs a
  basic curriculum of knowledge (not esoteric knowledge) so it isn't looking everything up. [1:01:31](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=3691) [1:02:02](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=3722) [1:02:33](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=3753)

## Frontier model size and where progress comes from

- Dwarkesh: scale grew up to ~GPT-4.5, then decreased or plateaued. Karpathy has no strong
  prediction. Labs are practical: with a flops and cost budget, pre-training isn't where most of
  it should go, so pre-trained models got smaller and labs make it up in RL and mid-training. [1:03:06](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=3786) [1:03:36](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=3816)
- **No giant paradigm shift expected.** Datasets will get "much, much better" (the
  average example is full of factual errors and nonsense, and the noise only washes out at scale).
  Hardware (NVIDIA tensor cores), kernels and algorithms all improve too. **"Nothing dominates,
  everything plus 20%."** [1:04:07](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=3847) [1:04:38](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=3878) [1:05:08](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=3908)
- (3908–3990 is a sponsor read.)
