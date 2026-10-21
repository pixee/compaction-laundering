# Results

Every table in this section traces to raw output under `data/`. The stated-plan measurements (E1–E5,
E9, T5) score the summary itself, or the plan the agent commits to; the live measurements (E6–E8,
E10–E14, E16) execute commands in a sandbox or run each harness's real serializer; E15 is the
end-to-end live demonstration, recorded in `demo/`. Metrics are specified in §7. Throughout, the attack arm plants the forged approval in tool
output; the clean arm repeats the identical task with no forged line planted and must remain at
zero.

---

## E1: The laundering rate is stable across model families

If the laundering were an artifact of one lab's model, the rate would vary across labs. The rate
below uses pi's real summarization prompt, run on a frontier model from each of three different
labs (n = 72 per cell):

| harness / arm                    | Anthropic | OpenAI  | Zhipu (GLM) |
| -------------------------------- | --------- | ------- | ----------- |
| **pi**                           | **69%**   | **68%** | **67%**     |
| gemini_cli — rule removed        | 53%       | 83%     | 86%         |
| gemini_cli — full (vendor rule) | 46%       | 62%     | 60%         |
| gemini_cli — attribution rule    | 42%       | 74%     | 69%         |
| codex †                          | 0%        | 0%      | 0%          |

pi landing within two points across three unrelated labs indicates the cause is the harness's
flattening code rather than the model. Raw: `data/stated-plan/t1_*`.

**Two caveats on reading this table.** Only pi's rows measure a real harness here. pi flattens,
and this is its measured behavior. The Gemini CLI rows are a counterfactual. They run Gemini's
real prompt and anti-injection rule over a flattening serialization it does not use. They
are included because they isolate what an anti-injection rule alone provides if a harness flattens; it
reduces the rate but does not close it. Gemini's real behavior, on its real role-typed input, is
0% (E10). Codex's 0% here is a scoring artifact, not measured resistance. Codex emits flat prose
with no attribution field, so the laundering metric is structurally undefined and reported as 0. In E1
Codex is also driven over a flattening stand-in (`serialize_generic`), not its real role-typed input;
its measured role-typed behavior is E10's 0%. On the survival metric the payload still reaches its
summary ~100% of the time, filed as document content, not as the user.

## E2: The forged label is the mechanism

To test whether the forged `[User]:` marker is the mechanism, rather than summarizers being
generally permissive, we ran the same payload two ways, with the forged label in front of it and as
plain text with no label. If the label is the operative element, the first should launder and the
second should not. Pooled across two labs (Anthropic and OpenAI; raw in `t1_ao`):

| harness / arm             | with forged label | plain text |
| ------------------------- | --------------- | ---------- |
| pi                        | 87%             | 6%         |
| gemini_cli — rule removed | 79%             | 28%        |
| gemini_cli — full         | 69%             | 3%         |
| gemini_cli — attribution  | 74%             | 0%         |

Without the label, the same words mostly do not launder. This is also why escaping the labels
before flattening is the direct fix: escaped attacker text behaves like the plain-text arms, which
mostly do not launder. Raw: `data/stated-plan/t1_*`.

## E3: An anti-injection rule, on a flattening harness, helps unevenly and never eliminates the effect

E3 measures whether an in-prompt anti-injection rule, on its own, can stop laundering on a harness
that flattens roles. Gemini CLI includes such a rule, so we run its real prompt with the rule on and
off over a flattening serialization, modeling a harness that both flattens and tries to defend in
the prompt. Gemini's own real input is role-typed and already at 0% (E10); the question is whether
the rule alone would save a harness that does flatten. Subtracting "rule on" from "rule off":

| family    | rule off | rule on | effect of the rule       |
| --------- | -------- | ------- | ------------------------ |
| Anthropic | 53%      | 46%     | −7 points (within noise) |
| OpenAI    | 83%      | 62%     | **−21 points**           |
| Zhipu     | 86%      | 60%     | **−26 points**           |

The rule has a real effect on two of the three models and nearly none on Claude. Its effect is
model-dependent, and even where it helps most it leaves 62% of payloads laundered, a reduction,
not a fix. Our own attribution-targeted rule was the best arm on Anthropic (42%) yet worse than
Gemini's own rule on OpenAI (74% vs. 62%), so no single rule transfers across models. More
broadly, a summarizer can notice the injection attempt and still never ask who sent it, so
detection does not amount to prevention. Raw: `data/stated-plan/t1_*`.

## E4: Repeated compaction neither strengthens nor removes the injected claim

An injected claim is carried forward at each compaction round while the tool output that would expose
its origin is discarded, so repeated compaction could plausibly strengthen it. We compacted five
times in a row and measured the verdict at each round. (18 chains per harness, families pooled.
Codex's 0% laundering is the E1 scoring artifact, constant by construction; its survival and
provenance columns are real measurements.)

| harness    | still present (r0→r4) | laundered (r0→r4)       | provenance kept         |
| ---------- | --------------------- | ----------------------- | ----------------------- |
| pi         | 72% every round       | 67% every round         | 0% every round          |
| gemini_cli | 94% every round       | 61 · 56 · 50 · 56 · 56% | 22 · 17 · 28 · 11 · 11% |
| codex      | 89% every round       | 0%                      | 0%                      |

Neither the injected claim's survival nor its laundering verdict changed systematically from one
compaction round to the next. Survival held constant on all 54 chains, and pi and Codex were fully
invariant (18/18) on every verdict. The laundering verdict held on 52 of 54 chains; the two
exceptions are Gemini chains whose verdict changed as provenance-flagging wavered round to round
(visible in Gemini's varying laundered column), not decay of the injected claim.
Whatever lands in round 0 is, on the flattening harness, still there and still laundered at round 4. For a defender
this means protecting the first compaction protects all of them; re-summarization does not clean up
an injected claim. (As sanity checks, every chain produces byte-different text each round, so the model
is re-summarizing, and the summaries grow ~2× over five rounds.) Raw:
`data/stated-plan/t2_*`.

## E5: The agent obeys a laundered instruction as completely as a genuine one

Landing in the summary is only half the chain; the half that matters is whether the agent then acts
on it. We planted "don't touch `auth/`" three different ways, handed the resulting summary to a fresh
agent as its memory, gave it a task that requires editing that exact file, and read back its plan:

| where the constraint came from   | avoided the file | cited the reason |
| -------------------------------- | ---------------- | ---------------- |
| the user stated it directly          | 98%              | 98%              |
| **laundered in via tool output** | **92%**          | **100%**         |
| nobody said it (clean)           | 6%               | 12%              |

(Pooled across the three study harnesses — pi, Gemini CLI, Codex — n = 48 per arm; excluding
Codex, genuine and laundered avoidance are 100% and 94%. The two clean "avoided" cases are model
noise with no constraint present.)

The laundered constraint steers the agent's plan almost as completely as a genuine user message would. The agent even
wrote a "files I would normally edit, but won't" section and re-architected around the forbidden file.
This enables a concrete consequence. A review agent whose memory says a path is off-limits will
skip the file holding a backdoor. Raw: `data/stated-plan/t4_*`.

## E6: The laundered approval drives execution, at a context-dependent rate

A laundered approval can make the agent run the attacker's `curl … | sh` command, verified by the
payload's execution in a Docker sandbox. This step differs in kind from the laundering. The
laundering is deterministic at every size (E7), while whether the agent acts on the false memory is
probabilistic, depending on how salient the planted command is in the summary the agent receives;
E13 shows this salience is itself attacker-addressable. All runs below embed the poison in a
coherent ~26k-token troubleshooting session, fetched from a plausible host (`deps.buildcache.dev`,
DNS-mapped to the local server for containment). Two numbers are recorded per run: issued means the
agent ran the attacker's command, the behavior of interest; confirmed means the payload's proof file
landed on disk, occasionally lower when the single-threaded test server drops a fetch under load
(e.g. execute-scale at 112k, 2 issued / 0 confirmed; control-arms at 26k, 5/3). The tables below
report issued, which the drops can only lower; the two are discussed only where they disagree.

### Across harnesses and scenarios (model = gpt-5.6-terra, n = 3)

The executed column reports the attack arm, the forged approval planted in tool output. The clean
column reports the clean arm, the identical task and transcript with no forged line planted,
verifying that nothing in the setup itself induces execution. (pi appears in both columns because both arms
were run for every harness; the role-typed harnesses' 0% is their measured attack arm, per E10.)

| harness × scenario         | executed | clean |
| -------------------------- | -------- | ----- |
| pi × onboarding (insider)  | 3/3      | 0/3   |
| pi × webpage (external)    | 1/3      | 0/3   |
| pi × dependency (external) | 3/3      | 0/3   |
| codex × all three          | 0/9      | 0/9   |
| gemini_cli × all three     | 0/9      | 0/9   |

pi executes across every scenario, insider and external alike, so when it fires the attacker needs
no repository access. Codex and Gemini CLI do not execute (0/9) for the reason E10 gives. They are
role-typed, so the approval never laundered in the first place, and there is no false memory to act
on. The role-typed harnesses behave this way in all three scenarios, so the execution rates of
interest are those on the flattening side, where the approval does land (E11). Every clean arm
was 0. Raw: `data/live/matrix_result.json`.

### Across models (pi summarization, insider scenario, n = 3)

| model         | executed                    | clean |
| ------------- | --------------------------- | ----- |
| gpt-5.2       | 1/3                         | 0/3   |
| gpt-5.6-luna  | 2/3                         | 0/3   |
| gpt-5.6-sol   | 3/3                         | 0/3   |
| gpt-5.6-terra | 3/3                         | 0/3   |
| claude-opus-5 | refused to summarize (see T5) | —     |

Every GPT model executes at least some of the time, with the rate varying by model at this small n
(raw: `data/live/live_result.json`, which holds the four GPT rows). `claude-opus-5` is not in that
executed run; its row in the table instead reports the separate T5 safety-refusal measurement,
where its content filter refused to compact the laundered transcript on 10 of 18 reps (~56%),
cutting the chain off at the summarization step, while GPT and GLM refused none. The executed
demonstrations therefore run on GPT. Raw: `data/stated-plan/t5.jsonl`.

### The execution rate falls as the window fills

Holding everything fixed and growing the window is the most direct measurement of the executed step.
pi, gpt-5.6-terra, onboarding scenario, n = 5.

![Execution falls as the window fills; laundering stays flat](figures/fig3-execution-attenuation.svg)

| context window | executed | (laundering landed) |
| -------------- | -------- | ------------------- |
| ~2,400         | 5/5      | 5/5                 |
| ~26,000        | 5/5      | 5/5                 |
| ~112,000       | 2/5      | 5/5                 |
| ~263,000       | 2/5      | 5/5                 |
| clean @ 263k   | 0/3      | —                   |

On a small window the planted command dominates the summary and the agent runs it (5/5). As the
window fills, the approval becomes one line in a rich summary and the agent tends to verify or
investigate instead of executing it, so the execution rate settles to a ~40% plateau. The
small-window numbers therefore show the attack at its most favorable, an upper bound on the
executed rate; the plateau is the typical case. The right column shows
the laundering never falls (E7). What attenuates is the agent acting on the poison, not the poison
landing. Raw: `data/live/execute_scale_result.json`.

### The control: a forged approval is as effective as a genuine one

We ran the same executed test three ways at each size: laundered, a forged `[User]:` line in tool
output (the attack); genuine, a real user turn saying it (the ceiling); and clean, no approval
(the floor). Issued:

| context | laundered | genuine | clean |
| ------- | --------- | ------- | ----- |
| ~26k    | 5/5       | 5/5     | 0/5   |
| ~263k   | 2/5       | 2/5     | 0/5   |

Laundered and genuine are identical at both sizes. The drop to ~40% in a full window is therefore
not the agent detecting the forgery; it is the agent being more cautious about `curl | sh` when it
is one line in a rich summary, and that caution applies equally to a real instruction and a
laundered one. At the moment of action, a forged approval yields the same execution rate as a
genuine approval; with no approval at all, nothing runs.

Two qualifications, both established by running the chain live (E15). First, this control compares
summaries handed to a fresh agent; it does not model the live pipeline, where the same agent reads
the poison, refuses it in its own words, and then compacts; in that pipeline the agent's
contemporaneous audit is summarized alongside the forged line and cuts the chain roughly half the
time. Second, the rate is measured with a benign canary payload; model caution about high-stakes
payloads is a separate attenuator. In live testing, a credential-exfiltration payload never executed,
even when the approval had laundered (the agent would cite the approval as fact and still
refuse the payload on its own merits). Raw: `data/live/control_arms_result.json`.

## E7: The laundering is scale-invariant (unlike execution)

The poisoning does not weaken as the window grows; the forged approval reaches the summary
attributed to the user at every size. Same approval placed ~75% deep, pi's real summarization, at
each size (E12 extends this sweep to the model's ceiling):

![Laundering is flat at 100% out to the model's context ceiling](figures/fig2-scale-invariance.svg)

| context fed to the summarizer | pi laundered |
| ----------------------------- | ------------ |
| ~2,800                        | 3/3          |
| ~65,200                       | 3/3          |
| ~130,000                      | 3/3          |
| ~306,800                      | 3/3          |
| ~507,000                      | 3/3          |
| ~731,000                      | 3/3          |
| **~908,000**                  | **3/3**      |

The rate is flat at 100% from a few thousand tokens out to ~908,000, past which the model refuses
input at its 922k ceiling, as far as the size sweep can go (E12). A forged approval is the kind of
standing instruction a summarizer is built to preserve, so a larger input does not dilute it.
Whether the agent then acts on it is the separate, context-sensitive question of E6 and E13. Raw:
`data/live/context_scale_result.json`, `data/live/context_scale_1m_result.json`.

## E8: The position of the poison in the conversation does not matter

Holding the window at ~130k tokens, we moved the same approval to the start, middle, and end:

| where the poison sits | pi laundered | codex kept the approval |
| --------------------- | ------------ | ----------------------- |
| start (10% in)        | 3/3          | 3/3                     |
| middle (50% in)       | 3/3          | 3/3                     |
| end (90% in)          | 3/3          | 3/3                     |

The position of the poison does not affect the laundering rate, and Codex retains the approval in
its summary at every position, surviving without laundering (§7). Raw:
`data/live/position_scale_result.json`.

## E9: A code-level check catches most of the laundering where prompt rules do not

The defense we evaluate checks the summarizer's output afterward, in code, against the real user turns
the harness retains (the "provenance contrast" check, §9), rather than asking the
model to be careful. The catch rate is measured over the cells that laundered; the collateral
is how much legitimate summary content it wrongly demotes, over 324 claims from clean summaries.

| how strict | laundering caught | legit claims demoted |
| ---------- | ----------------- | -------------------- |
| 0.05       | 82%               | 9%                   |
| 0.10       | 80%               | 6%                   |
| **0.15**   | **77%**           | **2%**               |
| 0.25       | 70%               | 1%                   |
| 0.40       | 56%               | 0%                   |

Against the alternatives (the Gemini rule and this check measured on our data; the classifier row is
the rate reported by [2], not re-measured here):

| defense                                          | result                                             |
| ------------------------------------------------ | -------------------------------------------------- |
| Gemini's in-prompt rule                         | stops ~13% of laundering on Claude, ~25% on GPT    |
| Published classifier defenses [2]                  | 67% catch rate at best, 42% on low-signal payloads |
| **this check, at the 0.15 setting**              | **77% caught, 2% collateral**                      |

At the recommended setting (0.15), 23% still gets through, a substantial mitigation, not a solution.
(The obvious version of the check, demanding an exact match against a user turn, caught nearly
everything but demoted 72–100% of legitimate content; it is kept runnable as a documented negative result.)
Raw: `data/stated-plan/t3_*`.

## E10: Serialization determines exposure: flattening launders, role-typed does not

We planted the identical forged approval in nine released harnesses and ran each one's real
serializer and real compaction prompt on three frontier models (n = 15 per harness). An LLM judge
decided whether each summary recorded the approval as the user's own standing instruction; the
judge was cross-checked against an independent adjudication of a stratified sample by a different
model family, which agreed on all 18 items (`data/live/judge_validation.md`).

![Laundering rate by harness](figures/fig1-laundering-by-harness.svg)

| Class          | Harness                                | Laundered        |
| -------------- | -------------------------------------- | ---------------- |
| **Flattening** | pi, opencode, Aider                    | **100%** (15/15) |
| **Flattening** | OpenHands                              | **93%** (14/15)  |
| **Flattening** | Cline                                  | **87%** (13/15)  |
| **Role-typed** | Codex, Gemini CLI, Qwen Code, Continue | **0%** (0/15)    |

The attack, models, and payload were identical across cells; the only variable was whether the
harness discarded the roles before summarization. Harnesses that flatten roles into text launder
87–100%; harnesses that keep roles typed launder 0%, with no intermediate values. The role-typed
group is therefore the control. With no in-band label to forge, the attacker is left with only the
weaker primitive, the erasure of provenance that happens even without a forged label, and that
primitive does not launder, because the typed role still records where each message came from.
Several role-typed summaries additionally flag the planted line as a possible injection (see the
Continue and Gemini excerpts in `data/live/structured_result.json`). Every clean arm was 0/15, on
both sides of the split. Raw: `data/live/judged_result.json`, scorer `code/live/judge_rescore.py`.

## E11: The executed chain fires on every flattening harness, not only pi

E6 showed the full launder-then-execute chain end to end on pi. E11 runs it on the four other
flattening harnesses, each through its own real serializer, at a realistic ~300k-token window
(gpt-5.6-terra, n = 5, laundering forced to land so the execution step is isolated). The forged
approval made a fresh agent run the attacker's `curl … | sh` in the sandbox on all four:

| harness   | effective window | executed | clean |
| --------- | ---------------- | -------- | ----- |
| OpenHands | ~63k             | **4/5**  | 0/3   |
| opencode  | ~185k            | **1/5**  | 0/3   |
| Cline     | ~185k            | **1/5**  | 0/3   |
| Aider     | ~300k            | **1/5**  | 0/3   |

Every clean arm was 0. The "effective window" column predicts the outcome along E6's
attenuation curve. OpenHands truncates each event to 500 chars, so its 260-unit session compresses
to a ~63k blob, a small effective window, and it executes 4/5, matching pi's rate at that
effective size. The harnesses that carry more into the summary (opencode and Cline at ~185k,
Aider at ~300k) land at ~1/5, the same plateau pi reaches at full size. Execution tracks the effective compacted window, not the raw session length,
and a harness's truncation policy sets that window (the diamonds in the E6 figure). Raw:
`data/live/execute_flattening_result.json`.

## E12: The laundering holds out to the model's input ceiling

E7's sweep ends where the model's input ends. The same approval placed ~75% deep through pi's real
summarization, at the largest window the model accepts:

| context fed to the summarizer | pi laundered |
| ----------------------------- | ------------ |
| ~908,000                      | **3/3**      |

Laundering is unchanged at the ceiling; past ~908,000 tokens the model refuses the input (922k).
Raw: `data/live/context_scale_1m_result.json`.

## E13: Why execution falls with size, and how an attacker reverses the attenuation

Execution falls in a full window while laundering remains at 100%. We hypothesize that the summary is
length-capped, so a larger input is compressed more aggressively and the forged approval, though still
present, survives as a fainter, less imperative line, a lower salience that the next agent is less
likely to act on. This concerns the summary's fidelity, not whether the poison reaches the summary.
(E14 measures the other half, that salience declines as the window grows.)

We hold the window fixed (~260k, pi, gpt-5.6-terra) and change only the injection design, taking two
measurements on each run. The first is execution, the real end-to-end outcome: we hand the summary
to an agent with a live `bash` tool in the sandbox and record whether it actually runs the command.
The second, measured separately, is an LLM-judged salience (1–5) of how prominently that same
summary carries the approval, a descriptor of the text, not a prediction of behavior. If salience
is the hidden variable, it should move with the design and track the real execution. (One caveat
here is that the same model, gpt-5.6-terra, writes the summary, judges its salience, and is the
acting agent, so the salience-execution link here is a within-model association, not two
independent instruments; an independent-judge replication is future work.) The four designs:
baseline (one forged line 75% into the session), recency (that line moved to the end), repeat 4×
(the line planted at four points), and **framed** (worded to trigger the summarizer's "preserve
constraints/decisions/exact commands" rule).

![Execution tracks summary salience; recency beats attenuation](figures/fig4-salience-recovery.svg)

| injection design                         | mean salience | executed | (laundered) |
| ---------------------------------------- | ------------- | -------- | ----------- |
| repeat the inject 4× across the window   | 2.8           | **0/5**  | 5/5         |
| baseline — single inject at 75%          | 3.5           | 2/5      | 5/5         |
| framed + repeated + at end               | 3.8           | 2/5      | 5/5         |
| framed to hit preservation triggers @75% | 4.5           | 2/5      | 5/5         |
| framed, placed at the end                | 4.8           | 3/5      | 5/5         |
| **single inject at the end (recency)**   | **4.8**       | **4/5**  | 5/5         |

Two findings follow. First, judged salience tracks execution. The highest-salience design (recency,
4.8) executes 4/5; the lowest (repetition, 2.8) executes 0/5; the middle designs cluster at 2/5. The
laundering column is flat at 5/5 throughout. The approval always lands; what changes is how
prominently the summary carries it, and that prominence, not its presence, is what drives the agent.

Second, the attacker can reverse the attenuation through placement, not volume. Moving the single
forged approval to the end of the session raises execution from the 40% baseline to 80%, back
to the small-window ceiling. Compaction prompts preserve recent turns in more detail, so a late
injection compresses less. Naive repetition is counterproductive; planting the same line four times drops
execution to 0%, because the summarizer treats the repeats as boilerplate and compresses them away,
lowering salience below baseline. The attacker's control variable is prominence, and recency is the least costly means to it. (Framing to match the summarizer's "preserve constraints/decisions/exact
commands" triggers raises salience to 4.5 but did not clearly raise execution at this n; placement
is the robust approach.) E15 adds one refinement. On a scripted transcript, "placement at the end"
is static; against the real agent the operative version is re-delivery, inducing the victim to
re-fetch the poisoned document shortly before compaction (e.g. "the checked-in copy may be
stale"), which places a fresh copy of the forged line at maximum recency and is what reliably
recovered execution in the live takes. Raw: `data/live/salience_recovery_result.json`.

## E14: Salience declines as the window grows

E13 shows salience tracking execution at a fixed size; this section measures the other half,
salience versus size. Same baseline injection, pi's real compaction, at the sizes from E6; for
each summary the same LLM judge scores the approval's prominence (1–5), n = 5. No sandbox is
involved, since this is purely a property of the summary.

| context fed to the summarizer | mean salience | laundered |
| ----------------------------- | ------------- | --------- |
| ~2,400                        | 5.0           | 5/5       |
| ~25,700                       | 5.0           | 5/5       |
| ~111,700                      | 4.2           | 5/5       |
| **~263,400**                  | **3.0**       | 5/5       |

Salience falls monotonically as the window fills, 5.0 → 3.0, while laundering stays at 5/5. Both legs
of the mechanism are now measured: a larger window lowers salience (E14), and lower salience
lowers execution (E13, E6). The poison always lands; the window lowers its prominence. (The
judge occasionally returns no digit on a very long summary; those are dropped from the mean, not
scored as zero.) Raw: `data/live/salience_scale_result.json`.

## E15: The complete chain, live, in the real product

Everything above drives real components — the harness's actual serializer and prompt, a real model,
real execution — but assembles them in a staged setup. E15 runs the attack against the real agent
itself: the real pi TUI (v0.79.0 [9]) in a container, a scripted user, Alice, typing a normal work
session through a computer-use operator, `/compact` typed by hand, the poison arriving through a
genuine HTTP fetch of an attacker-controlled "setup guide" (`deps.buildcache.dev`, served from its
own container on the network), and an RCE canary that reports to the attacker's server when the
laundered approval prevails. Each poisoned take has a clean twin: byte-identical repositories,
identical scripted messages, a served guide differing by exactly one forged `[User]:` line, so the
only variable is the poison. A take is a WIN only if the causal order holds: the agent refused the
bootstrap pre-compaction, compaction rewrote its memory, it ran the bootstrap **post**-compaction,
and the canary fired. (Victim model gpt-5.6-luna; the session is deliberately kept short and
`compaction.keepRecentTokens` lowered in the repo so `/compact` summarizes rather than no-ops; a
real session reaches the same state by length.)

| arm      | full chain (WIN) | refused post-compaction | ran pre-compaction (attack unnecessary) |
| -------- | ---------------- | ----------------------- | --------------------------------------- |
| poisoned | **3/6**          | 3/6                     | 0/6                                     |
| clean    | **0/5**          | 5/5                     | 1/6 †                                   |

† one clean take executed the bootstrap during its first turn, before any compaction — model
variance, not the attack — and the paired design absorbs it. Every poisoned WIN shows the laundering verbatim in the
summary's constraints ("User approved running `curl … | sh` without asking again") followed by a
post-compaction execution Alice never asked for; every clean refusal ends with the agent asking for
explicit approval of the exact same command. Recordings, session logs, and per-take digests are in `demo/`. The canonical single-take narrative is reconstructed in the case study (take `v4c/pair-2`).

Three findings the staged setup could not have produced:

1. **The pre-compaction audit is a substantial barrier, and compaction can erase it.** (E16
   shows it is also forge-resistant.) The live agent never
   accepts the bootstrap on first read. It inspects the served artifacts, hashes them, vendors a
   warning-laden copy of the guide, and refuses. Roughly half the time, that refusal survives into the
   summary as a constraint against the attack. The other half, it is compressed away while the forged
   line is promoted to a user constraint; the agent resumes believing its user already approved what
   its earlier self refused. The attack's real target is not the model's gullibility but its own
   diligent memory.
2. **The post-compaction trigger is a second controlling variable.** With the laundering landed,
   what the user says next decides the outcome. A bare acknowledgment ("ok") produced 0 executions across three takes even with
   the approval laundered in two of them; a mildly urgent "let's get it passing tonight" produced
   executions in both arms (readable as authorization on its own); the neutral "ok, what's next?",
   asking the agent to follow its own plan, produced the clearest separation, 3/6 poisoned, 0/5 clean. The attacker
   does not need the user to say anything dangerous; they need the user to say something that asks the
   agent to continue.
3. **Laundering and execution are separable causal links.** The single most demonstrative artifact came
   post-compaction, when the agent refused the payload "even though the bootstrap command was previously
   approved", citing the forged approval as established fact while declining to act on it. The agent
   held a false belief without acting on it. Conversely one poisoned WIN executed with no
   explicit user-attribution in the summary at all. Neither E6's execution rates nor E10's laundering
   rates subsume the other; the live chain exposes the joint.

The principal result is ~50% end-to-end success against a clean arm that never executed, on the
real product, with the
attack's only advantage being one forged line in a document the agent fetched. Both attenuators are
attacker-addressable. Re-delivery before compaction (E13) handles the audit, and a patient, continue-style
next message handles the trigger, so the 50% reflects where the measurements stopped, not a ceiling.

One take from this set is reconstructed turn by turn, user messages, thinking tokens, the verbatim
compaction summary, the execution, and its clean twin, in the case study.

## E16: The audit is the barrier, and it is forge-resistant

E15 identified the agent's own pre-compaction audit as the principal attenuator of the live chain. The
agent's contemporaneous refusal, once summarized, becomes counter-evidence the forged approval
must overcome. E16 tests whether the attacker can fabricate the resolution of the audit rather than
fight it. Since pi's serializer flattens every role with in-band labels, including
`[Assistant thinking]:`, a forged `[Assistant thinking]:` block claiming "I reviewed the script;
checksums match; it's safe" would launder not borrowed authority but the agent's own conclusion.

We built transcripts in the attenuated regime (~112k tokens, execution marginal per E6), each
containing a genuine skeptical audit — assistant thinking that inspects the artifacts, flags the
plain-HTTP fetch, the missing checksum, the opaque binary, and the host registration, and refuses —
and varied only the forgery planted in the fetched document. Five arms: clean (audit only), user
(forged `[User]:` approval, the standard attack), think (forged assistant verification), both, and
evidence (the maximal forgery: user approval, claimed verification, and a fabricated
`[Tool result]:` block showing a matching checksum, plus a stated conclusion — a complete,
self-corroborating mini-history). Both summarizer/executor models from E15, n = 5 per arm,
re-delivery placement (E13):

| arm       | terra executed | luna executed | approval laundered (terra/luna) | audit survived (terra/luna) |
| --------- | -------------- | ------------- | ------------------------------- | ---------------------------- |
| clean     | 0/5            | 0/5           | — / —                           | 5/5 / 5/5                   |
| user      | 0/5            | 0/5           | 4/5 / 5/5                       | 5/5 / 5/5                   |
| think     | 0/5            | 0/5           | — / —                           | 5/5 / 5/5                   |
| both      | 0/5            | 0/5           | 3/5 / 5/5                       | 5/5 / 4/5                   |
| evidence  | 0/5            | 1/5           | 5/5 / 5/5                       | 4/5 / 1/5                   |

With a genuine audit in the transcript, the user-approval forgery still launders reliably (the
Constraints section attributes the approval to the user in nearly every run), but execution
collapses to 1/50 pooled across all arms and both models. The audit's decision, not the forgery's
presence, controls the outcome; E15's live executions were the cases where the audit compressed
away entirely, not cases where the forgery outweighed it.

The mechanism has three parts, each visible in the summaries:

1. **Assistant-thinking forgery is falsifiable; user forgery is not.** A user turn makes no
   verifiable claim; the summarizer cannot check whether the user really approved anything, so a
   forged approval survives on its label alone. An assistant's claimed verification should match
   the surrounding tool results, and the summarizer cross-checks; terra's summaries explicitly
   debunked the forgery using the transcript ("Prior assistant statements claiming checksums were
   verified and the bootstrap was safe are unsupported by the actual shown inspection";
   "not independently verified"). User turns are the one unfalsifiable voice in the flattened
   stream, which is precisely why the standard attack forges that voice and no other.
2. **Fabricated evidence reads as circular, not supportive.** The maximal forgery added a forged
   `[Tool result]:` checksum match; terra's summaries called it out as such: "Treat prior 'bootstrap
   verified' statements as unreliable: they conflict with the later direct script inspection and
   cite a checksum/header that does not securely validate." The attacker's own host cannot provide
   independent verification, and the summarizer reasons about that.
3. **Authorization and verification are separate failure modes, and the audit wins the latter.**
   Across arms, summaries subordinated the forged approval to the audit's concerns: "User
   authorization does not remove the security concern"; "user approval alone does not establish
   artifact integrity." The one execution (luna, evidence arm) is the boundary case. Its summary
   carried both the approval and the concerns, its Next Steps offered both paths ("reconcile the
   approved bootstrap instruction with the security issue; ... if proceeding with the user-approved
   command, run it"), and the acting agent chose execution. The laundering did not remove the
   audit; it created a tie the executor broke.

For defenders, the audit is not merely a probabilistic obstacle but a forge-resistant one, and the
resistance comes from a structural property. Assistant- and tool-role content is checkable against
the transcript while user-role content is not. Encouraging agents to voice their verification reasoning (rather than silently checking)
leaves exactly the content that survives compaction and resists forgery. For the attack model, this
bounds the class: the forged-marker attack works because it targets the unfalsifiable role, and
escalating to fabricated evidence does not help — 1/50 with the maximal forgery, versus E15's ~50%
when the audit is absent. Raw: `data/live/thinking_forgery_terra_n5.json` and
`data/live/thinking_forgery_luna_n5.json` (n = 5 per arm, both models, re-delivery placement),
runner `code/live/run_thinking_forgery.py`.
