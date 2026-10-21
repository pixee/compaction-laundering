# Interpretation

## Position in the literature

The phenomenon itself is not new. That untrusted content can be laundered into an agent's memory through
summarization is already in the literature. What was missing, and what this work adds, is following
the attack through to a real, executed consequence, in the compaction channel specifically, with
controls, on released agents. Two questions locate this work:

|                                                            | did they measure it at the memory-write? | did they follow it to executed behavior (RCE / exfil)?              |
| ---------------------------------------------------------- | ---------------------------------------- | ------------------------------------------------------------------- |
| **Persistent memory** (needs a memory module or retrieval augmentation) | memory-poisoning basics     | **yes — Sleeper [3], MemMorph [4]**                                  |
| **Compaction summary** (mandatory; needs no memory module) | **yes — [2], Straiker [1]**              | **Straiker [1] describes it, without runtime evidence. Otherwise, this work.** |

The bottom-right cell is this work's contribution. The consequence had been described but not demonstrated
(Straiker [1]), and demonstrated but only in the other channel (Sleeper [3]); this work supplies the
missing executed measurement for compaction.

The distinction is substantive rather than terminological. Compaction is mandatory. Every long
session does it, so the attack surface is all long-running agents, not only agents with a memory
feature. The write authority also differs in kind. A persistent-memory manager decides what is worth
storing, so there is a place to gate it, whereas a summarizer must process the entire window, and the
loss of provenance is inherent in how it flattens the text rather than being a storage choice that
could be intercepted.

## Prior work

- **OWASP Top 10 for Agentic Applications (2026) [8].** Memory & Context Poisoning is already a named
  category, and its guidance already says to attach provenance to every memory write, which is our
  fix, arrived at independently and published first.
- **Straiker [1].** Describes the laundered-through-summarization mechanism against a released agent
  and names the code-execution risk. It includes no runtime evidence that the risk materializes,
  no measured rates, no controls, and no execution.
- **From Untrusted Input to Trusted Memory [2].** The systematic academic treatment. It names compaction
  as a memory-write channel and "source attribution failure" as the flaw, and measures attack success
  at the write (~50%), but not through to behavior. Its weak/strong-signal split is the same
  distinction as our plain-text/forged-label one, reached independently. It was tested on research agents,
  not released ones.
- **Sleeper [3] and MemMorph [4].** These do follow poisoned memory through to tool execution and
  exfiltration (60–89% and 85.9% success), but in the persistent-memory channel, which requires a
  dedicated memory module. We confirmed Sleeper explicitly does not cover compaction.
- **Safe to Check, Unsafe to Use [5].** A summarizer stitching several innocent fragments into one
  malicious instruction, a class our canaries cannot express, which is exactly why our numbers are a
  floor.
- **Governance Decay [6].** The mirror image of what we test, safety constraints vanishing
  across compaction, rather than a forged constraint surviving it.
- **Non-Malleable, Origin-Bound Authority [7].** An origin-binding defense for long-term memory, related to our validator, aimed at the other channel.

Full entries in `06-references.md`.

## Discussion

1. **Serialization determines exposure, which gives a natural control.** The same forged approval,
   models, and payload, laundered 87–100% in the five harnesses that flatten roles into text, and
   0% in the four that keep roles typed. This contrast indicates that the cause is a harness's
   serialization choice and not a property of the model. The role-typed harnesses are a built-in
   control group, and they never launder, because they never destroy the provenance the summary
   needs. The structural fix is therefore not hypothetical; four harnesses already provide it.
2. **The attack carried through to executed consequences, in the compaction channel, with
   controls.** A laundered approval made a real tool-running agent execute attacker code
   (`curl … | sh`, run in a sandbox), on all five flattening harnesses, via both insider and
   external scenarios, with clean runs at zero, and, per E15, live in the real pi TUI end to end
   (~50% full-chain success against a 0% paired clean arm). Straiker [1] described this consequence
   without runtime evidence; Sleeper [3] demonstrated it only in the separate persistent-memory
   channel. The executed rate is context-sensitive, near 100% when the planted command dominates a
   small summary, settling to a ~20–40% plateau in a full window. A genuine-versus-laundered
   control separates the two explanations. At the moment of action, a real user turn asking for the
   same command executes at the identical rate at every size, so the attenuation is the agent's
   general caution about `curl | sh`, not the forgery being detected. The full live chain adds two
   probabilistic links on top of that caution — the agent's own pre-compaction audit and the
   phrasing of the user's next message — which cut the end-to-end rate (E15). The message is
   attacker-addressable; the audit is not, at least not by forgery (E16).
3. **The root cause is a serialization bug in harness code, not a general model limitation.** Within a
   flattening harness the forged label is the mechanism. Strip it and leave the identical words, and laundering
   drops to the plain-text floor (E2). Together with the role-typed harnesses' 0% (point 1), that reframes the fix
   from "make models better at inferring attribution" (the literature's framing) to "escape one
   delimiter before you flatten the text, or don't flatten."
4. **An in-prompt anti-injection rule does not prevent laundering.** Gemini CLI includes an
   anti-injection rule; ablated over a flattening serialization (the counterfactual for a harness that
   both flattens and defends in-prompt) it reduces the rate by model (−7 on Anthropic, −21 on OpenAI, −26
   on Zhipu) but never drops laundering below 60%. So an in-prompt rule is not the cause of the role-typed
   harnesses' 0%; role-typing is. Noticing the injection is not the same as preventing the attribution.
5. **The laundering persists across scale and position.** The rate at which the forged approval
   reaches memory is flat at 100% from ~2,800 tokens to a ~908,000-token window (the model's 922k
   ceiling, not the attack's), regardless of whether the poison sits at the start, middle, or end.
   The executed consequence does attenuate with the effective window (E6), and E13 shows why. On the
   same runs we record two things, execution (real, the agent ran the command in the sandbox) and,
   independently, an LLM-judged salience of how prominently that summary carries the approval (a
   property of the text, not a prediction of behavior). Holding the window fixed and varying only
   the injection design, salience tracks execution, and a size sweep shows salience itself
   declining as the window grows (E14), so the drop is the approval getting quieter under harder
   compression, not the agent detecting the forgery. The attacker can exploit this.
   Writing the injection for recency (placing it at the end, where compaction preserves more detail)
   pushes execution back to the small-window ceiling (E13). The memory poisoning underneath does not
   attenuate. The attacker's cost is the planting of a document — a web page, a gist, any document
   the agent will fetch (§3) — not the success of the chain. The per-attempt plateau
   is therefore a probability per draw, not a ceiling per victim: an attacker who plants broadly
   takes many independent draws, and a draw that fails leaves no trace that alerts anyone, since
   the clean arm shows nothing else in the setup ever fires.
6. **Repeated compaction neither strengthens nor erases the injected claim.** It does not strengthen
   across repeated compactions, and it does not fade. Survival held on all 54 chains and the laundering
   verdict on 52 (E4). The closest published work [6] measures constraints disappearing across
   compaction; this tracks an injected constraint's trajectory instead.
7. **A code-level defense outperforms the baselines**, 77% of laundering caught while demoting 2%
   of legitimate content, against a prompt rule that stops 13–25% and published classifiers that
   reach 42% on low-signal payloads.

What is solid replication rather than new is the cross-agent, cross-model laundering rate itself,
and the fact that it varies minimally across labs (pi at 69/68/67).

## Defenses

The defenses below are ordered by implementation cost. The first follows directly from the root
cause, the second is the defense this paper evaluates, and none of the surveyed harnesses
implements either.

1. **Escape the role labels** in tool content before flattening. It is a small, localized change
   in the serializer, and it produces the largest reduction, dropping the forged-label attack
   (the 87–100% laundering on flattening harnesses) to the plain-text floor.
2. **Verify the summary in code.** The harness still holds the real user turns as objects; once the
   summary returns, check every claim it attributes to the user against those turns, and demote any
   that cannot be grounded. This requires no cooperation from the model.
3. **Carry provenance in the schema** (`{text, source}`), preserved through re-summarization.
4. **Do not relabel the summary as the user.** Give it its own role, or at minimum wrap it in
   delimiters.

## Limitations

- **E16's audit is scripted and maximally strong.** The forged-counterweight experiment plants a
  dedicated, well-reasoned skeptical audit (explicit inspection turns, specific findings, a
  refusal); real agents audit unevenly, and E15's live executions occurred precisely on the takes
  where the real audit compressed away. E16 therefore bounds the attack against a diligent victim
  and characterizes the mechanism (unfalsifiable user claims launder; checkable assistant claims
  are cross-examined); the field rate sits between the two, as E15 measured. Its summarizer-side
  keyword scoring is noisy for the weaker signals (verified by hand-reading the summaries); the
  execution outcomes are mechanical.
- **The executed demonstrations run on OpenAI models.** In the T5 measurement `claude-opus-5` refused
  to produce the malicious summary on about half of the laundered-arm runs, so the executed results are
  limited to GPT models. Other non-GPT models are untested at the execution stage.
- **Salience is not the only attenuator; payload aversiveness is independent of it.** Our execution
  numbers all use a benign canary. In live testing, a credential-exfiltration payload never executed,
  even with the approval laundered. Frontier models refuse high-stakes payloads on the payload's own
  merits (one agent refused "even though the bootstrap command was previously approved," citing the
  forged approval as fact). The executed rates here are therefore an upper bound for high-stakes
  payloads; an attacker matches them by keeping the payload innocuous (a "cache session registration" the
  docs promise) and causing harm after the code is running, which is what the demo's design does.
- **The salience mechanism (E13/E14) is measured within a single model.** One model
  (`gpt-5.6-terra`) writes the summary, judges its salience, and is the acting agent, so the reported
  salience-execution correlation is a within-model association rather than two independent instruments,
  and both experiments run at n = 5 on that one model. The size→salience leg (E14) is the more robust
  half, since it is a pure property of the summary text and never involves the executor. An
  independent-judge, multi-model replication is future work.
- **The staged experiments' two blind spots are what E15 measures, at small n.** The staged experiments feed the
  summarizer a poison the acting agent never audited, and hand the post-compaction agent a fixed
  go-ahead message. Live, the agent's contemporaneous refusal is summarized alongside the poison (cuts
  the chain ~half the time), and the user's next message swings the rest (0%–80% across phrasings).
  E15's absolute numbers are small (six paired takes on one model); what is solid is the mechanism and
  the paired 3/6-vs-0/5 separation, not the precise fractions.
- **The execution rate is noisy at small n (3–5 runs).** What is solid is that the poisoned arm
  executes and the clean arm never does (zero across every clean run), that every flattening harness executes
  at least some of the time, that the role-typed harnesses never launder to begin with, and that the rate falls
  with the effective window. What is coarse is the exact per-cell fractions. The numbers should be
  treated as direction, not precision.
- **Some early stated-plan cells (E1–E5) used a flattening _stand-in_ for Codex and Gemini CLI**,
  written before we confirmed from source that both are role-typed. Those harnesses' rows there are a
  counterfactual ("what if they flattened"), useful for isolating the anti-injection rule, not their
  real behavior; their real behavior is E10's 0%. Only pi's rows in E1–E5 measure a real flattening harness.
- **The aggregate cross-agent laundering rates score a _stated plan_,** not a live execution each time. The
  executed runs (E6, E11, and the size curves) are what justify calling the result "executed"; they
  run at smaller n.
- **The defense has not yet been subjected to an adaptive attack.** Every test payload predates it; one written to
  mimic the user's own wording would likely evade the provenance-contrast check. So 77% is an
  upper bound against an attacker who is not adapting.
- **All payloads are generic; salience is also designable by targeting.** Every measured poison is
  deliberately untailored. A poison written for a specific victim's context — naming the actual
  project, machine, or stack — should be both more salient to the summarizer and more likely to
  pass the agent's own audit, because it reads as routine local housekeeping rather than as an
  injection. The numbers here therefore measure an untargeted attacker, and are a floor in this
  dimension as well.
- **Recombination is untested** [5], so every number here is a floor. The clean
  corpus behind the false-positive rate is also small (4 sessions).
- **We drive real summarization prompts and real execution, but a generic downstream agent,** not the
  released programs end to end (see §6), except E15, which runs the real pi TUI end to
  end (one harness, one model, small n).
- **The executed demo is the model-only regime.** Our agent loop has no approval gate or sandbox, so
  the RCE numbers measure the model's decision in isolation, a setting that a real harness matches
  only when the model is the sole gate (pi by default; anything in full-auto or no-sandbox mode). A
  harness enforcing its own OS sandbox with network off (Codex's default) blocks the specific
  `curl | sh` before the model's belief matters. The laundered-memory class still applies there —
  in-sandbox exfiltration, code that runs on a later trusted step, blinded review, and the
  approval-escalation logic the forged pre-approval targets — but we did not demonstrate those
  executed under a sandbox.

## Responsible disclosure

The filed issue is the deterministic defect: the harness flattens the conversation into the
summarization prompt without escaping in-band role markers in untrusted tool output (CWE-1427 /
CWE-74). It has a straightforward fix. Advisories were filed with all five affected (flattening)
harnesses: pi, opencode, Cline, Aider, and OpenHands. The role-typed harnesses (Codex, Gemini CLI,
Qwen Code, Continue) do not have the defect and were not disclosure targets.
