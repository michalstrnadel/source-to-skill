https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=5570

# 08: Evolution of intelligence, culture, self-play (1:32:50–1:42:55)

Chapter "Evolution of intelligence & culture". Karpathy had recommended Nick Lane's
book to Dwarkesh, who then interviewed Lane.

## Is intelligence a rare accident?

- Karpathy: intelligence is very recent, and **"I am surprised that it evolved."** [1:33:02](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=5582) [1:33:32](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=5612)
- **Use how long a step was bottlenecked as a prior.** Following Nick Lane, imagine a thousand
  Earth-like planets: most would have bacteria-like life. Bacteria and archaea sat for about
  2 billion years with "nothing happening" despite huge biochemical diversity, so the next step
  looks hard. Multicellular animals have existed for maybe a couple hundred million years, ~10% of
  Earth's lifespan. What surprises him is a creature that creates and accumulates culture
  and knowledge. [1:33:32](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=5612) [1:34:03](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=5643) [1:34:34](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=5674) [1:35:37](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=5737)
- Dwarkesh relays Sutton ("if you got to the squirrel, you'd be most of the way to AGI")
  and squirrel-level intelligence soon after the Cambrian explosion ~600 million years ago. [1:34:34](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=5674) [1:35:06](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=5706)
- **Count independent origins:** hominids and birds (ravens are "extremely clever" with
  quite distinct brain parts) suggest intelligence may have arisen a few times. [1:36:08](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=5768)
- Dwarkesh relays Gwern and Carl Shulman: the scalable algorithm may exist in birds too, but
  humans had a **niche that rewarded marginal intelligence**. A bird with a bigger brain can't fly,
  and dolphins can't have fire. Hands → tool use → externalized digestion → more energy for the brain
  is the flywheel. Karpathy agrees, though he'd have expected evolution to get stuck on "animals with bigger
  muscles". [1:36:39](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=5799) [1:37:09](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=5829) [1:37:40](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=5860)
- **Why lifetime learning evolves:** environments must be unpredictable and change fast, so evolution
  can't bake the algorithms into the weights. Many animals are "pre-baked", while humans must figure it
  out "at test time" after birth. [1:38:10](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=5890) [1:38:41](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=5921)

## LLMs don't have culture

- Dwarkesh (citing Quintin Pope): modern cognitive architecture existed ~60,000 years ago
  and agriculture came ~10,000 years ago. The gap was spent building a cultural scaffold, which LLM
  training gets "for free". [1:38:41](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=5921) [1:39:12](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=5952) [1:39:43](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=5983)
- Karpathy: **"yes and no". LLMs don't really have culture**, and that's an impediment. In the
  simplest form, culture would be a giant scratchpad the LLM edits while it works. "Why can't an LLM
  write a book for the other LLMs?" [1:39:43](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=5983) [1:40:00](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=6000) [1:40:30](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=6030)
- **Two unclaimed multi-agent ideas:** [1:40:30](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=6030) [1:41:00](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=6060)
  1. **Culture**: a growing repertoire of knowledge for the LLMs' own purposes.
  2. **Self-play**: like AlphaGo playing itself, since evolution is driven by competition.
     For example, one LLM generates ever-harder problems for another to solve. "No one has done it yet."
- Organizations also belong in the culture bucket, and none of it has been shown convincingly.
  We're still mostly in the single-agent realm, "so that's why we're still early". [1:41:31](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=6091)
- **Bottleneck:** models cognitively resemble kindergarten or elementary-school students. Claude
  Code and Codex can pass PhD quizzes but still feel like an elementary-grade student, **"savant kids"**
  with perfect memory who produce convincing slop. Kids can't create culture. [1:42:01](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=6121) [1:42:32](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=6152)
