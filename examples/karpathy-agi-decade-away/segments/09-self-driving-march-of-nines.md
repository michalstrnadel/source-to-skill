https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=6175

# 09: Why self-driving took so long: the march of nines (1:42:55–1:56:20)

Chapter "Why self driving took so long". Karpathy led self-driving at Tesla from 2017 to
2022 (Dwarkesh's framing). He spent five years on it, and many of his intuitions come
from there.

## It isn't done, and it didn't take "a decade"

- **First pushback: "this is not even near done."** [1:43:02](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=6182)
- The first demos go back to the 1980s (a CMU truck driving itself in 1986). Around
  2014 a friend at Waymo gave him a "perfect" drive around Palo Alto, and he thought it
  was very close. It still took a long time. [1:43:32](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=6212) [1:44:02](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=6242)
- The real endpoint is **self-driving at scale**, where people don't need a driver's license. The
  start was in the 1980s and the end isn't here yet. [1:51:00](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=6660)

## The demo-to-product gap and the march of nines

- **There is a very large demo-to-product gap where the cost of failure is high.** That property
  makes timelines longer. [1:44:02](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=6242)
- **Production software shares that property.** Vibe coding doesn't, but in real production code
  a mistake can mean security vulnerabilities and hundreds of millions of people's
  social security numbers leaking. In software, how bad an outcome can get "is almost unbounded". [1:44:32](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=6272) [1:45:03](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=6303)
- **March of nines:** a demo that works 90% of the time is just the first nine, and
  **every nine is a constant amount of work**. At Tesla over ~5 years they went through
  "maybe three nines or two nines", with more to go. [1:45:03](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=6303) [1:45:33](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=6333)
- **"I'm very unimpressed by demos."** A cooked-up demo is worst. An interactive one is a bit
  better, but you still need a product that survives contact with reality and its many
  pockets of behavior needing patches. [1:45:33](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=6333) [1:46:03](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=6363)
- Dwarkesh: humans make a mistake every ~400,000 miles (~7 years of driving). A coding agent
  emitting code constantly would hit its "7 years" of tokens much faster in wall-clock time.
  Karpathy: general software engineering has more surface area than self-driving, which is one vertical. [1:46:34](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=6394) [1:47:05](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=6425)

## Do LLMs give us the hard parts for free?

- Dwarkesh: much of self-driving's decade went into robust perception and common sense,
  which LLMs/VLMs now provide, so deploying AI into a new domain is like taking a car to a new city.
  Karpathy is "not 100% sure": LLMs are still fallible with gaps, and there's no "magical
  generalization completely out of the box". [1:47:35](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=6455) [1:48:06](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=6486) [1:48:36](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=6516)
- **Deployments are still minimal.** Waymo has few cars and isn't economical (capex plus
  operations). Driverless cars hide "very elaborate teleoperation centers". "We haven't actually
  removed the person, we've moved them to somewhere we can't see them." He says he doesn't know
  the full extent, nor Waymo's stack specifics. [1:49:06](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=6546) [1:49:37](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=6577) [1:50:00](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=6600)
- He loves Waymo and rides it all the time, but on the record: **Waymo got an early start by
  packaging many sensors, and Tesla took "the more scalable strategy"**. That still has to play out. [1:50:30](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=6630)

## Where the analogy breaks: bits vs. atoms

- Dwarkesh: knowledge work has no hard latency constraint like a car's onboard model, and serving
  another model copy is cheap compared to building another car. [1:51:31](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=6691) [1:52:01](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=6721) [1:52:32](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=6752)
- Karpathy agrees: **"bits are like a million times easier than anything that touches the
  physical world"**, so adaptation should be faster. Knowledge work at scale will still have practical
  latency and compute constraints. [1:52:32](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=6752) [1:53:03](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=6783)
- **Borrow the rest of the analogy:** societal, legal and insurance layers. "What is the
  equivalent of people putting a cone on Waymo?" What is the hidden teleoperator? [1:53:03](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=6783) [1:53:33](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=6813)

## Overbuilding compute?

- Dwarkesh: compute is going 10× in a year or two and maybe 100×+ by the end of the decade. Is that a telecom-bubble-style
  overbuild? [1:54:04](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=6844) [1:54:34](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=6874)
- Karpathy: he sounds pessimistic but is **"actually optimistic... I think this will work...
  it's tractable"**. He's reacting to Twitter-timeline hype driven by fundraising and "converting
  attention to money". He doesn't think there's overbuilding: Claude Code and OpenAI Codex didn't exist a
  year ago, and demand (already visible in ChatGPT) will absorb it. He wants calibration because very
  reputable people have gotten timelines wrong over his 15 years, and because of geopolitical
  ramifications. [1:54:34](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=6874) [1:55:05](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=6905) [1:55:36](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=6936) [1:56:07](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=6967)
