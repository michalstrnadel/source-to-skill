https://www.youtube.com/watch?v=zjkBMFhNj_g&t=2535s

# 14 — LLM OS

**Thesis:** it's inaccurate to think of an LLM as a chatbot or word
generator. It is closer to the **kernel process of an emerging operating
system**, coordinating memory and computational tools for problem solving.

## What an LLM might look like in a few years

- Reads and generates text; knows more than any single human about all
  subjects.
- Browses the internet or references local files (RAG).
- Uses existing software infrastructure (calculator, Python, ...).
- Sees and generates images and video; hears, speaks, generates music.
- Thinks for a long time using a System 2.
- Maybe self-improves in narrow domains that have a reward function.
- Can be customized and fine-tuned for many tasks — many LLM experts in an app
  store, coordinating for problem solving.

## OS equivalences

| Classic computer | LLM OS |
|---|---|
| Disk | Internet / files, accessed via browsing / retrieval |
| RAM | **Context window** — the finite, precious working memory |
| Kernel paging memory | LLM paging relevant information in and out of its context window |
| Also: multithreading, multiprocessing, speculative execution, user vs kernel space | Rough equivalents exist (not covered in detail) |

## Ecosystem analogy

| Desktop OS | LLMs |
|---|---|
| Proprietary: Windows, macOS | Proprietary: GPT series, Claude series, Bard |
| Open source: diverse Linux-based ecosystem | Open: fast-maturing ecosystem, mostly Llama-based |

**Use:** borrow analogies from the previous computing stack to reason about
this new one — LLMs orchestrating tools, accessed through a natural-language
interface.
