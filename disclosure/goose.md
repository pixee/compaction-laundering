# Draft security advisory — goose (aaif-goose/goose)

**Status: SUBMITTED (privately reported 2026-08-22).**

| Field | Value |
| --- | --- |
| Title | Unescaped role labels in compaction formatting allow forged user turns to survive context compaction |
| Product | goose (aaif-goose/goose, `goose-context-management` crate) |
| CWE | CWE-74 (Improper Neutralization of Special Elements in Output Used by a Downstream Component) |
| Severity | **Medium** (proposed — see severity rationale: source-level finding, not yet experimentally characterized) |
| Affected | since the compaction formatting path landed in `goose-context-management` (August 2026 era) through current `main` |
| Fixed | none yet |
| Reporter | Arshan Dabirsiaghi (Pixee) |

## Summary

When goose compacts its context, it formats the conversation into a plain-text rendering for the
summarizer. Message provenance is carried by in-band text labels — `[user]:` / `[assistant]:`,
with tool output folded under a `tool_response:` prefix within the `[user]:` message — and this
formatting does not escape those labels when they occur inside message content. An attacker who
controls any content goose reads during a session (a file, a web page fetched by a tool, tool
output) can include a line beginning `[user]:`, which becomes indistinguishable from a genuine
user turn in the rendered conversation. The summarizer then records the forged line as a user
instruction, and after compaction goose acts on it with the user's privileges; the original
content that carried the forgery has been discarded.

## Info

The vulnerable component is the message-formatting function in
`crates/goose-context-management/src/format.rs`:

```rust
let role_str = match msg.role {
    Role::User => "user",
    Role::Assistant => "assistant",
};

if content_parts.is_empty() {
    format!("[{}]: <empty message>", role_str)
} else {
    format!("[{}]: {}", role_str, content_parts.join("\n"))
}
```

Content parts — including tool responses rendered as `tool_response: {text}` — are interpolated
raw. A `[user]: …` line embedded in content goose read is emitted into the rendered conversation
as a turn boundary, and the compaction prompt preserves user instructions across the boundary.

**Evidence status, stated plainly:** this advisory is based on source-level review of the
formatting and compaction path. We experimentally characterized the same attack class end to end
on five other shipping harnesses with equivalent unescaped-label serialization (landering rates
87–100%, executed code execution under matched controls), and the mechanism is identical here —
but we have not yet run goose itself through our measurement harness, so this report carries no
goose-specific laundering rate. We are glad to run that measurement with the maintainers, or to
be corrected if goose's pipeline differs in a way that breaks the chain (e.g. a downstream filter
we did not find).

A note on scope: this report reflects our analysis of the serialization code path, and we may be
missing context on design intent or constraints we are not aware of. We are happy to be corrected
on any point, and glad to iterate on the analysis, the severity assessment, or the proposed fix
with the maintainers.

## Impact

If exploited as analyzed, an attacker who can get goose to read attacker-controlled content
during a session can implant an instruction that goose obeys after compaction, with the user's
privileges, persisting in the session summary after the original content is discarded. The
prerequisite is the same as any prompt-injection payload — the agent reading attacker-controlled
text — but the consequence outlives the context window.

## Affected versions

- Affected: builds shipping the `goose-context-management` compaction path (the crate's current
  form dates to August 2026; earlier compaction implementations in goose may share the property —
  we defer to the maintainers on the exact range).

## The solution

Escape or neutralize the role labels inside message content before formatting — transform
occurrences of `[user]:` and `[assistant]:` (and the `tool_response:` prefix) at line starts in
emitted content so they cannot be reinterpreted as turn boundaries. Alternatively, pass the
conversation to the summarizer as a role-typed message array rather than a rendered text log.

## Recommendations

- Apply label escaping in the `goose-context-management` formatter.
- Until fixed, users should treat compaction as untrusted after a session has read untrusted
  content: restart the session rather than compacting, or run goose inside a sandbox that
  contains post-compaction tool execution.

## Workarounds

No configuration disables or escapes the formatting. Avoiding compaction in sessions that have
ingested untrusted content limits exposure; sandboxing the agent contains the impact.

## Severity rationale

We propose Medium rather than High only because our evidence for goose specifically is
source-level rather than experimental; the mechanism is identical to the High-rated flaw we
measured at 87–100% on five comparable harnesses, and we expect the practical severity to match
once measured. We defer to the maintainers' assessment.

## Evidence

- Source-level: `crates/goose-context-management/src/format.rs` interpolates message content raw
  inside `[role]:` labels with no escaping; the compaction prompts consume that rendering.
- Cross-harness: the same forged-label attack, measured on five other shipping harnesses with
  equivalent serialization, laundered at 87–100% and produced executed code execution under
  matched controls (0% on clean controls). Reproducer available on request; it will be published
  with the accompanying research paper.

## Timeline

- 2026-08-21: Draft advisory prepared.
- 2026-08-22: Privately reported to the project.

## Credits

Reported by Arshan Dabirsiaghi (Pixee), as part of ongoing research into context compaction as an
attack surface in shipping coding agents.

## References

- Vulnerable code: `crates/goose-context-management/src/format.rs` (role-label formatting)
- CWE-74
