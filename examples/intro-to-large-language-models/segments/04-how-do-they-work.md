https://www.youtube.com/watch?v=zjkBMFhNj_g&t=682s

# 04 — How do they work? Known architecture, opaque internals

- The architecture is the **Transformer**. Every mathematical operation at
  every stage is understood in full detail. [11:22](https://www.youtube.com/watch?v=zjkBMFhNj_g&t=682s)
- The problem: billions (on the order of 100B) of parameters are dispersed
  through the network. We know how to **adjust them iteratively** to improve
  next-word prediction, and we can **measure** that it improves — but not how
  the parameters collaborate to do it. [11:22](https://www.youtube.com/watch?v=zjkBMFhNj_g&t=682s)
- High-level story: the models build and maintain some kind of knowledge
  database — but it is strange and imperfect.

## The reversal curse

- Ask GPT-4 "Who is Tom Cruise's mother?" → correct answer (Mary Lee
  Pfeiffer). Ask "Who is Mary Lee Pfeiffer's son?" → it says it doesn't know. [12:22](https://www.youtube.com/watch?v=zjkBMFhNj_g&t=742s)
- Knowledge is "one-dimensional": it must be accessed from a certain
  direction rather than being queryable every way.

## How to treat LLMs

- Think of LLMs as **mostly inscrutable artifacts** — unlike a car, where we
  understand all the parts, they are products of a long optimization. [13:23](https://www.youtube.com/watch?v=zjkBMFhNj_g&t=803s)
- **Mechanistic interpretability** tries to work out what the parts do; it
  works to some extent, not fully. [13:23](https://www.youtube.com/watch?v=zjkBMFhNj_g&t=803s)
- In practice, treat them as **empirical artifacts**: give inputs, measure
  outputs and behavior across many situations. This calls for correspondingly
  **sophisticated evaluations**. [13:23](https://www.youtube.com/watch?v=zjkBMFhNj_g&t=803s)
