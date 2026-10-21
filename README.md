# Compaction Laundering

Security research into context compaction (conversation summarization) in open-source coding agents.
When a flattening harness compacts, untrusted text an attacker slipped into a file it read can come out
the other side recorded as the user's own instruction, and drive the agent to execute attacker-controlled
code. Harnesses that keep messages role-typed through compaction do not (0% in our tests), which pins the
flaw on the harness's serialization, not the model.

The paper is the six Markdown files below. Start with [`01-thesis.md`](01-thesis.md), which also maps the
rest of the repository (`code/`, `data/`, `demo/`).

1. [`01-thesis.md`](01-thesis.md) — abstract and introduction
2. [`02-design.md`](02-design.md) — threat model, method, metrics, the experiment list
3. [`03-results.md`](03-results.md) — every measurement, as tables traceable to `data/`
4. [`05-case-study.md`](05-case-study.md) — one live take, turn by turn
5. [`04-interpretation.md`](04-interpretation.md) — prior art, the fix, limitations, disclosure
6. [`06-references.md`](06-references.md) — bibliography
