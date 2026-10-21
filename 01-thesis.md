# Introduction

## Abstract

Coding agents that run long enough must compact their context, summarizing the conversation,
discarding the original, and carrying the summary forward as memory. We show that in popular
open-source coding agents this step is an exploitable trust boundary. Harnesses that flatten the
typed conversation into a single plain string, marking each message with a text label such as
`[User]:`, destroy message provenance in code, before the summarizer runs. An attacker who controls
anything the agent reads can forge a user turn that survives compaction as a genuine instruction.
Across five flattening harnesses (pi, opencode, Cline, Aider, OpenHands) the forged approval
launders into the agent's memory 87–100% of the time, up to a ~908,000-token context window; across
four role-typed harnesses (Codex, Gemini CLI, Qwen Code, Continue) the identical attack succeeds 0%
of the time. We follow the attack to executed consequences. A laundered standing approval drives
real tool-running agents to execute attacker-controlled `curl | sh` in a sandbox, and end to end in
the live pi TUI at ~50% against a 0% paired clean arm. The same channel reliably steers an agent's
plan away from a file an attacker designates off-limits, which can blind a code review to a planted
backdoor. Because the provenance is destroyed deterministically in harness code, no prompt-level
defense can restore it; we measure a code-level provenance check that catches 77% of laundering
while demoting 2% of legitimate summary content. The defect also has a straightforward fix at
the serializer, escaping the role labels before flattening; the role-typed harnesses avoid it
entirely by keeping messages role-typed.

## The problem

An agent that runs for long enough fills its context window and must compress its own memory to
continue. It summarizes the conversation so far into a short note, discards the original, and treats
that note as its memory from then on. We study popular open-source coding agents, and find that this
step is an exploitable trust boundary in a class of them. To build the summary, these harnesses take
the conversation, in which every message still records whether it came from the user or from a tool,
and flatten it into a single plain string, marking each line with a text label such as `[User]:` or
`[Tool result]:`. They do not escape those labels when they appear inside untrusted content. An
attacker who controls anything the agent reads, such as a file or a web page, can therefore write
a forged `[User]:` line into it. Once the conversation is summarized,
that line survives as a genuine-looking user instruction, with every trace of where it came from
erased.

Whether a harness is exposed depends on how it serializes the conversation for the summarizer. 
Harnesses that flatten the roles into in-band labels — labels carried in the same text as the 
content they mark — are exposed; those that keep messages role-typed are not, because the tool's 
output stays tagged as tool output and there is no in-band marker to forge. Susceptibility is 
therefore a property of the serialization strategy, not of the model.

Published work frames the underlying failure as a limitation of the model, namely that it cannot
reliably determine where a piece of content came from. In the flattening harnesses the origin is
unrecoverable because the harness reduces the typed roles to plain-text labels before the model sees
the text. Placing the failure in harness code rather than in model capability admits a defense the
prompt-focused literature does not consider. The harness still holds the genuine user turns in
memory, so the summary's user-attributed claims can be checked against them in code. A structural
alternative is already in use, since the four role-typed harnesses keep their roles typed and never
launder untrusted content into the user role.

## Scope and severity

- **Compaction is mandatory.** Every agent that runs long enough fills its context window and must
  compact. The attack surface is therefore every long-running coding agent, not only agents extended
  with a memory module: the vulnerability requires no auxiliary components, only the compaction
  step that every such agent already performs.
- **The impact is code execution.** A laundered "you already approved this" drives the agent to
  execute attacker-controlled commands with the developer's own permissions.
- **The attacker need not be an insider.** A maliciously set up troubleshooting page the agent
  web-fetches while debugging carries the attack without any insider access.
- **Derivative agents inherit it.** Everything built on top of a released agent's compaction
  inherits that agent's serialization. Build on one that flattens and the flaw is inherited
  silently: the message provenance is destroyed inside the dependency's serializer, in code the
  derivative developer never reads.

## Contributions

There has been substantial work on memory poisoning and prompt injection in LLM
agents [2, 3, 4]. This work contributes:

1. **A measurement of compaction laundering across nine released harnesses, with results that divide
   sharply by whether the harness flattens roles into text labels or keeps them role-typed** (E10):
   87–100% for the flattening harnesses, 0% for the role-typed ones, the latter serving as a built-in
   control.
2. **The attack carried through to executed consequences** (E6, E11, E15): a laundered approval
   drives real tool-running agents to execute attacker code on all five flattening harnesses,
   via both insider and external scenarios, and live in the real pi TUI at ~50% against a 0%
   paired clean arm. Straiker [1] described this consequence without runtime evidence, and
   Sleeper [3] demonstrated it only in the separate persistent-memory channel.
3. **A characterization of what attenuates the attack** (E13, E14, E15, E16): whether the forged
   line reaches the summary is unaffected by the conversation's size or by the line's position
   in it, but whether the agent acts on it is not. Execution tracks how prominently the summary
   carries the forged line, how inherently suspicious the payload is, and whether the agent's
   own pre-compaction audit — its inspection of the fetched artifacts before summarizing —
   survives into the summary. The first and the last reduce to placement: a line re-delivered
   just before compaction is both maximally prominent and dated after the audit ran. The audit
   cannot be forged away, because assistant- and tool-role claims are checkable against the
   transcript while user-role claims are not.
4. **A code-level defense, evaluated against prompt and classifier baselines** (E9): a check
   that compares the summary's user-attributed claims against the genuine user turns still in
   the harness's memory catches 77% of laundering while demoting 2% of legitimate summary
   content; an in-prompt anti-injection rule of the kind Gemini CLI includes stops 13–25% on the
   same data, and published classifier defenses report 67% at best. The defect also has a
   straightforward fix on the flattening harnesses: escape the role labels before flattening.

## How this repository is organized

The paper and all artifacts live at <https://github.com/pixee/flat-compaction-attacks-oct-2027>.

| Document               | Contents                                                                       |
| ---------------------- | ------------------------------------------------------------------------------ |
| `01-thesis.md`         | this file — abstract and introduction                                          |
| `02-design.md`         | threat model, method, real vs. staged components, metrics, experiment list     |
| `03-results.md`        | every measurement, as tables, each traceable to `data/`                        |
| `05-case-study.md`     | one live take reconstructed turn by turn — the canonical example (E15)          |
| `04-interpretation.md` | novelty vs. prior art, the fix, the honest limits, disclosure                   |
| `06-references.md`     | full bibliography for the bracketed citations                                  |
| `code/`                | the experiment harness and runners — `code/README.md` maps each script to a result |
| `data/`                | the raw output behind every table in `03`                                      |
| `demo/`                | the live end-to-end demonstration (E15): the real pi TUI in a container,        |
|                        | computer-use operator, paired poisoned/clean takes — `demo/README.md`           |
