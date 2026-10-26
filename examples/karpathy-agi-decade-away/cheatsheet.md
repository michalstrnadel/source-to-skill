# Cheatsheet: Karpathy on the Dwarkesh Podcast (Oct 2025)

Rules of thumb, numbers and named ideas from the whole episode. Timestamps link
into the audio.

## Using LLMs and agents

- **Pick the mode by the code.** Use agents for boilerplate and patterns common online. Use autocomplete when
  the code is novel or precisely arranged: you stay the architect. [30:00](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=1800) [30:32](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=1832) [31:05](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=1865)
- **Use LLMs to enter unfamiliar languages**, but only with a reference implementation you
  understand plus tests (his Python → Rust tokenizer). [33:45](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=2025)
- **Point and type, don't describe.** Navigating to the spot and typing three letters beats writing English
  instructions. [32:41](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=1961) [33:14](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=1994)
- **Put the material in context.** Paste the chapter or the whole repo (GPT-5 Pro, "the Oracle") rather
  than relying on the model's hazy recall. [18:44](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=1124) [36:02](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=2162)
- **Expect agent failure modes on unique code:** defaulting to the common approach (DDP), try/catch
  bloat, "production code base" style, deprecated APIs. [31:38](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=1898) [32:09](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=1929) [32:41](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=1961)
- **Ask your dumb questions to an LLM with the paper in context**, then share the thread with the
  author. [2:20:34](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=8434)

## Forecasting AI

- **Translation invariance in time:** to predict 10 years ahead, look 10 years back (2015 had
  convnets and ResNets, but no transformers). [24:19](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=1459)
- **No single driver:** data, hardware, kernels and algorithms contribute roughly equally, so
  "everything plus 20%". [25:51](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=1551) [1:05:08](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=3908)
- **The 1989 LeCun convnet redo:** 33 years of algorithms halved the error, and more needed 10× data plus
  longer training with regularization. [24:49](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=1489) [25:21](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=1521)
- **March of nines:** a 90% demo is nine #1, and every further nine costs the same work. Tesla went
  through "maybe three nines or two nines" in ~5 years. [1:45:03](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=6303) [1:45:33](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=6333)
- **Discount demos:** a cooked-up demo is worst, an interactive one is better, and neither is a product. [1:45:33](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=6333)
- **High cost of failure means long timelines.** This applies to production software as well as driving. [1:44:02](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=6242) [1:44:32](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=6272)
- **Where automation comes first:** short task horizon, little context, closed, purely digital
  (call centers, not radiology). [1:09:49](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=4189) [1:10:00](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=4200)
- **Autonomy slider:** AI does 80% of the volume and delegates 20%, with humans supervising ~5 AIs. [1:10:30](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=4230)
- **Look for the hidden human:** teleoperation centers, cones on cars, legal and insurance layers. [1:49:37](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=6577) [1:53:33](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=6813)
- **AGI definition he keeps:** any economically valuable task at human performance or better. Digital
  knowledge work alone is ~10–20% of the economy (his guess). [1:07:14](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=4034) [1:07:46](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=4066) [1:08:16](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=4096)

## Training and research

- **Outcome-only RL** up-weights every token of a successful rollout, including wrong turns:
  "sucking supervision through a straw". [42:12](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=2532) [42:45](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=2565)
- **LLM-judge rewards** survive ~10–20 RL steps, not 100–1,000, before adversarial outputs
  ("da-da-da" scoring 100%) appear. Patching the judge just yields new adversarial examples. [45:59](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=2759) [47:02](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=2822) [48:06](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=2886)
- **Check synthetic data for collapse** across many samples, not one: "ask it 10 times... all of them
  are the same". [52:09](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=3129) [52:39](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=3159)
- **Raising entropy has a cost:** the model drifts into its own language and rare words. [58:38](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=3518)
- **Cognitive core:** strip memory, keep algorithms; ~1B params; distill from better models trained on
  cleaned data. [56:20](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=3380) [59:10](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=3550) [1:01:01](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=3661) [1:01:31](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=3691)
- **Unclaimed multi-agent ideas:** LLM culture (shared, growing scratchpads; books for other LLMs) and
  self-play (LLMs posing harder problems for each other). [1:40:30](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=6030) [1:41:00](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=6060)

## Numbers

| Number | Context | Who |
|---|---|---|
| ~15 years | Karpathy's time in AI | Karpathy [2:34](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=154) |
| 15T tokens / 70B params → ~0.07 bits per token | Llama 3 weights vs. data | Dwarkesh [17:02](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=1022) |
| ~320 KB per token | KV cache growth in context, a ~35 million× gap | Dwarkesh [17:37](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=1057) |
| 33 years, error halved, 10× data | LeCun 1989 convnet redo | Karpathy [25:21](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=1521) |
| ~8,000 lines | nanochat, the full ChatGPT-clone pipeline | Karpathy [28:03](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=1683) |
| 8 GPUs | nanochat training; custom gradient sync instead of DDP | Karpathy [31:38](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=1898) |
| ~10–20 vs. 100–1,000 steps | RL against an LLM judge before it breaks | Karpathy [45:59](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=2759) |
| ~1B params | cognitive core prediction | Karpathy [59:10](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=3550) |
| "everything plus 20%" | per-factor improvement | Karpathy [1:04:38](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=3878) |
| 10–20% | knowledge work's share of the economy (guess) | Karpathy [1:07:46](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=4066) |
| 80% / 20%, teams of 5 | AI-human call-center split | Karpathy [1:10:30](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=4230) |
| ~2% | constant growth rate for 200–300 years | both [1:24:34](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=5074) |
| 1986 / ~2014 | CMU self-driving truck / his perfect Waymo demo ride | Karpathy [1:43:32](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=6212) |
| 400,000 miles (~7 years) | average human driving mistake interval | Dwarkesh [1:46:34](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=6394) |
| 100 lines | micrograd: all of backprop; "everything else is efficiency" | Karpathy [2:17:17](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=8237) |

## Teaching and learning

- **Build it to understand it:** rebuild from reference, no copy-paste, and skip blog posts and slides. [28:03](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=1683) [29:39](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=1779)
- **Ramps to knowledge:** each step depends only on the previous ones, and you optimize Eurekas per second. [2:02:33](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=7353) [2:18:20](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=8300)
- **Present the pain before the solution**, and let learners guess first. [2:18:50](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=8330) [2:19:22](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=8362)
- **Find the first-order term** (physics thinking, the spherical cow), serve it on a platter, then add terms. [2:15:45](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=8145) [2:16:46](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=8206)
- **Explain it like over lunch.** The three-sentence version is the real abstract. [2:21:39](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=8499) [2:22:12](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=8532)
- **Alternate learning modes:** depth-wise on demand (project reward) and breadth-wise. [2:23:45](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=8625)
- **Teach to learn:** if you can't explain it, you don't understand it. [2:24:15](https://api.substack.com/feed/podcast/176425744/3127b612a1604474d2b28ab4e9b658f4.mp3#t=8655)
