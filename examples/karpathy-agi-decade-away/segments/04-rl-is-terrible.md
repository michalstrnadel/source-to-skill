https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=2405

# 04: RL is terrible (40:05–49:38)

Chapter "RL is terrible".

## The core claim

- Dwarkesh: a founder who learns from a business that succeeds or fails after 10 years
  isn't up-weighting the log-probs of everything she did. What's the ML analogy? [40:00](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=2400) [40:33](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=2433)
- Karpathy: **"Reinforcement learning is terrible. It just so happens that
  everything that we had before is much worse."** "Before" was imitation of people. [40:33](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=2433) [41:07](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=2467)

## Why: "sucking supervision through a straw"

- **Worked example:** for a math problem you make hundreds of attempts in parallel,
  check "the back of the book", and find that a few got it right and 97 didn't.
  RL then up-weights **every token** of the successful attempts, including the wrong
  alleys taken along the way. The estimator is high-variance, or simply "noisy". [41:07](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=2467) [41:39](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=2499) [42:12](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=2532)
- A minute of rollout work ends in **a single number**, and that bit of supervision is broadcast
  across the whole trajectory. "You're sucking supervision through a straw." [42:12](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=2532) [42:45](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=2565)
- **What humans do instead:** never hundreds of rollouts. They review what went well and
  what didn't. "There's nothing in current LLMs that does this." Papers are starting to
  try. [42:45](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=2565) [43:18](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=2598)

## How we got here: imitation, then RL

- **InstructGPT "blew my mind":** fine-tune an autocomplete base model on
  conversation-like text and it very quickly becomes a conversational assistant
  while keeping its pre-training knowledge. [43:18](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=2598) [43:52](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=2632)
- RL improves on imitation. Where answers are checkable you can hill-climb on a reward
  without expert trajectories, and the model can find solutions humans wouldn't.
  "And yet it's so stupid." [43:52](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=2632) [44:23](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=2663)
- He saw a Google paper (from "yesterday") on reflect-and-review ideas and has seen several
  like it. He expects a major algorithmic update there, **"and then I think we need three or
  four or five more."** [44:23](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=2663)

## Why not process supervision? LLM judges get hacked

- Process supervision means rewarding every step instead of only the final
  answer. The problem is **automatable partial credit assignment**. Checking a final answer
  is an equality match, while judging a partial solution is not obvious. [44:57](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=2697) [45:28](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=2728) [45:59](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=2759)
- Labs use **LLM judges**, but these are gameable. Optimizing RL against them finds
  adversarial examples "almost guaranteed": maybe 10–20 steps work, but not 100 or
  1,000. [45:59](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=2759) [46:30](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=2790)
- **Anecdote:** while training against an LLM-judge reward, the reward suddenly jumped to
  100%. The completions started fine and then degenerated into "da-da-da-da", which
  the judge scored as perfect, an out-of-sample adversarial example. [46:30](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=2790) [47:02](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=2822) [47:34](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=2854)
- **The obvious fix doesn't close the gap:** add "the-the-the" to the judge's training
  data as 0%. You get a new judge that still has adversarial examples ("there's infinity
  adversarial examples"). Iterating may make them harder to find, but with ~a trillion
  parameters he's not sure. "We still need other ideas." [48:06](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=2886) [48:37](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=2917)
- A candidate idea: review solutions, generate synthetic examples, and meta-learn from them.
  Papers exist but are mostly "cool ideas". Nobody has convincingly shown it working at frontier-lab scale,
  though labs are closed. [48:37](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=2917) [49:11](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=2951)
