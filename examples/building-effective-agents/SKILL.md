---
name: building-effective-agents
description: Anthropic's guide "Building Effective AI Agents" (Dec 2024) - the workflow vs. agent distinction, the augmented LLM building block, five workflow patterns (prompt chaining, routing, parallelization, orchestrator-workers, evaluator-optimizer), when an autonomous agent is justified, and how to design agent tools (ACI). Load when designing or reviewing an LLM application or agent, choosing between a single call, a workflow and an agent, picking a framework, or writing tool definitions.
---

# Building Effective AI Agents

Source: [Building Effective AI Agents](https://www.anthropic.com/engineering/building-effective-agents)
— Anthropic Engineering, 2024-12-19, by Erik S. and Barry Zhang.
The article itself notes that much of the tooling landscape it describes has
changed since December 2024; the patterns and principles below are what it
teaches, not a survey of current tools.

## Thesis

Across dozens of customer teams, the agent systems that worked best were not
built on complex frameworks but on simple, composable patterns. Start with
the simplest thing that works and add complexity only when it measurably
improves outcomes.

## Vocabulary: workflows vs. agents

Both are "agentic systems"; the split is about who controls the path.

- **Workflow** — LLMs and tools orchestrated through predefined code paths.
  Predictable and consistent; best for well-defined tasks.
- **Agent** — the LLM dynamically directs its own process and tool use and
  decides how to accomplish the task. Flexible; best when model-driven
  decisions are needed at scale.

## Decision ladder: how much system do you need?

Climb only when the rung below demonstrably falls short.

1. **Single optimized LLM call** with retrieval and in-context examples —
   usually enough for many applications. Not building an agentic system at
   all is a legitimate answer.
2. **Workflow** — the task decomposes into steps you can define in code.
3. **Agent** — open-ended problem, the number of steps cannot be predicted,
   no fixed path can be hardcoded, and you trust the model's decisions.

Agentic systems trade latency and cost for task performance; check that
trade makes sense before taking it.

## Key claims and their support

### 1. Prefer raw API calls over frameworks, at least at first

- Frameworks (the article lists the Claude Agent SDK, AWS Strands Agents
  SDK, Rivet, Vellum) simplify low-level chores: calling LLMs, defining and
  parsing tools, chaining calls.
- Cost: extra abstraction hides the actual prompts and responses, so they
  are harder to debug, and they make it tempting to add needless complexity.
- Many patterns are a few lines of code against the API directly.
- If you use a framework, understand the code underneath — wrong
  assumptions about what it does are a common source of customer errors.
- Moving to production: be willing to strip abstraction layers and rebuild
  on basic components.

### 2. Everything is built from the augmented LLM

- Building block = an LLM plus retrieval, tools and memory; current models
  generate their own search queries, choose tools and decide what to keep.
- Two things matter: tailor the augmentations to your use case, and give
  the LLM an easy, well-documented interface to them.
- Model Context Protocol is offered as one way to plug into third-party
  tools with a simple client.

### 3. Five workflow patterns cover most production systems

| Pattern | How it works | Use when | Article's examples |
|---|---|---|---|
| Prompt chaining | Sequence of calls, each consuming the previous output; optional programmatic "gate" checks between steps | Task splits cleanly into fixed subtasks; you accept latency for accuracy by making each call easier | Write marketing copy, then translate it; outline a document, check the outline against criteria, then write it |
| Routing | Classify the input, send it to a specialized follow-up prompt/tool/model | Distinct categories are better handled separately and can be classified accurately (by LLM or classic classifier); tuning for one input type would hurt others | Split support queries into general / refund / technical; send easy questions to a small cheap model (Claude Haiku 4.5) and hard ones to a stronger one (Claude Sonnet 4.5) |
| Parallelization: sectioning | Independent subtasks run at once, outputs aggregated in code | Speed, or a task with several considerations that each deserve a focused call | One call answers while another screens for inappropriate content (beats one call doing both); automated evals with one call per aspect |
| Parallelization: voting | Same task run several times for diverse outputs | Multiple attempts or perspectives raise confidence | Several prompts review code for vulnerabilities; several prompts judge content appropriateness with tunable vote thresholds for false positives vs. negatives |
| Orchestrator-workers | A central LLM breaks the task down at runtime, delegates to worker LLMs, synthesizes results | Subtasks cannot be predicted in advance (e.g. which files a code change touches) — the difference from parallelization is that subtasks are decided by the orchestrator, not predefined | Coding products making multi-file changes; search gathering and analyzing many sources |
| Evaluator-optimizer | One call generates, another evaluates and gives feedback, in a loop | Clear evaluation criteria and iteration adds measurable value. Two fit tests: human feedback demonstrably improves the output, and an LLM can produce that kind of feedback | Literary translation with an evaluator critiquing nuance; multi-round search where the evaluator decides if more searching is needed |

These are not prescriptive; shape and combine them, measure performance,
and iterate.

### 4. Agents are simple in structure; the hard part is the environment and tools

- An agent is typically just an LLM using tools in a loop, driven by
  environmental feedback.
- Lifecycle: start from a user command or discussion; once the task is
  clear, plan and act independently; get "ground truth" from the
  environment every step (tool results, code execution) to judge progress;
  pause for human input at checkpoints or blockers; stop on completion or a
  stopping condition such as a maximum iteration count.
- Enabled by maturing capabilities: understanding complex inputs,
  reasoning and planning, reliable tool use, recovering from errors.
- Risks: higher cost and compounding errors. Mitigate with extensive
  testing in sandboxed environments and appropriate guardrails.
- Autonomy makes agents ideal for scaling tasks in trusted environments.
- Anthropic's own examples: a coding agent resolving SWE-bench tasks
  (edits across many files from a task description), and the "computer use"
  reference implementation.

### 5. Agents pay off where four conditions hold

Tasks that need both conversation and action, have clear success criteria,
allow feedback loops, and include meaningful human oversight.

- **Customer support** — conversational flow plus external data and
  actions; tools fetch customer data, order history, knowledge base
  articles; refunds and ticket updates are programmatic; success is
  measurable as user-defined resolution. Some companies charge only per
  successful resolution, signalling confidence.
- **Coding** — solutions verifiable by automated tests, tests double as
  feedback for iteration, the problem space is structured, quality is
  objectively measurable. Anthropic's agent solves real GitHub issues in
  SWE-bench Verified from the PR description alone — but human review is
  still needed to check fit with broader system requirements.

### 6. Tool design (the agent-computer interface) deserves as much care as prompts

- Invest as much in the ACI as teams invest in human-computer interfaces.
- Choosing formats — equivalent formats are not equally easy for a model
  to write (a diff needs the changed-line count in the hunk header before
  the code; code inside JSON needs escaped newlines and quotes):
  - leave the model enough tokens to think before it commits;
  - stay close to formats common in natural internet text;
  - avoid formatting overhead such as counting thousands of lines or
    string-escaping code.
- Writing definitions:
  - put yourself in the model's shoes — if the tool needs careful thought
    to use, it does for the model too;
  - include example usage, edge cases, input format requirements, and
    boundaries versus other tools;
  - tune parameter names and descriptions like a great docstring for a
    junior developer, especially when tools are similar;
  - test with many example inputs (e.g. in the Workbench), watch the
    mistakes, iterate;
  - poka-yoke: change arguments so mistakes are harder to make.
- Evidence: for the SWE-bench agent, the team spent more time on tools
  than on the overall prompt. The model erred with relative file paths once
  it left the root directory; requiring absolute paths made it use the tool
  flawlessly.

## Three principles for implementing agents

1. Keep the agent's design simple.
2. Make it transparent — show the agent's planning steps explicitly.
3. Craft the ACI carefully through thorough tool documentation and testing.

## Anti-patterns called out

- Reaching for an agent (or any multi-step system) before trying a single
  well-optimized call.
- Using a framework you do not understand; debugging through abstractions
  that hide the prompts.
- Adding complexity that does not demonstrably improve measured outcomes.
- One call handling both guardrails and the core response.
- Running agents without sandboxed testing, guardrails, or stopping
  conditions.
- Tool formats that force counting, escaping, or committing before
  thinking; ambiguous parameters across look-alike tools.

## More

- [highlights.md](highlights.md) — short quotes worth keeping.
