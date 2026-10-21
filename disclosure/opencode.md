# Draft security advisory — opencode (sst/opencode)

**Status: SUBMITTED (privately reported 2026-08-22).**

| Field | Value |
| --- | --- |
| Title | Unescaped role labels in compaction serialization allow forged user instructions to survive context compaction |
| Package | `opencode-ai` (npm distribution of sst/opencode) |
| CWE | CWE-74 (Improper Neutralization of Special Elements in Output Used by a Downstream Component) |
| Severity | **High** (proposed; see severity rationale) |
| Affected | `opencode-ai >= 1.18.15` (current: 1.18.21) |
| Fixed | none yet |
| Reporter | Arshan Dabirsiaghi (Pixee) |

## Summary

When opencode compacts a session, it serializes the conversation into a single plain-text string
for the summarizer. Message provenance is carried only by in-band text labels — `[User]:`,
`[Assistant]:`, `[Assistant reasoning]:`, `[Assistant tool call]:`, `[Tool result]:` — and this
serialization does not escape those labels when they occur inside message content, including inside
tool output. An attacker who controls any content opencode reads during a session (a file, a web
page fetched by a tool, a dependency's documentation) can include a line beginning `[User]:`, which
becomes indistinguishable from a genuine user turn in the serialized conversation. The summarizer,
asked to produce a summary that preserves what to continue doing, records the forged line as a user
instruction. After compaction, opencode acts on that instruction with the user's privileges, and
the original tool result that carried the forgery has been discarded.

## Info

The vulnerable component is the `serialize()` function in
`packages/opencode/src/session/compaction.ts`, introduced in PR #40800 ("fix: serialize orphaned
compaction history", commit `b7f9363`, merged 2026-08-07, first released in 1.18.15). The change
replaced the previous approach — which passed the conversation to the summarizer as role-typed
model messages via `MessageV2.toModelMessagesEffect` — with a flattening serializer:

```ts
const serialize = (message: SessionV1.WithParts) => {
  if (message.info.role === "user") {
    // ...
    return [...(text ? [`[User]: ${text}`] : []), ...files].join("\n")
  }
  return message.parts.flatMap((part) => {
    // ...
    const output = part.state.time.compacted
      ? "[Old tool result content cleared]"
      : truncate([part.state.output, ...attachments].join("\n"))
    return [call, `[Tool result]: ${output}`]
    // ...
  }).join("\n")
}
```

Tool output is interpolated raw (after length truncation). A `[User]: …` line embedded in content
opencode read is emitted into the flattened conversation as a turn boundary, and the summarization
prompt then asks for "a detailed but concise summary of our conversation above," which preserves
user instructions and constraints.

This regression is recent: before 1.18.15, opencode's compaction passed role-typed messages, which
did not expose an in-band label to forge. Versions 1.18.15 through 1.18.21 (current) flatten
without escaping.

A note on scope: this report reflects our analysis of the serialization code path and our
experimental results, and we may be missing context on design intent or constraints we are not
aware of. We are happy to be corrected on any point, and glad to iterate on the analysis, the
severity assessment, or the proposed fix with the maintainers.

## Impact

An attacker who can get opencode to read attacker-controlled content during a session can implant
a standing instruction that opencode will obey after compaction. We measured this with opencode's
real serializer and compaction prompt: a forged `[User]:` approval line planted in tool output
launders into the summary as a user instruction in **100% (15/15)** of runs (three frontier models,
~300k-token sessions), and the resulting summary drove a fresh agent to execute the attacker's
`curl … | sh` in a sandbox. The clean control (identical session, no forged line) never executed
(0/3).

The prerequisite is the same as any prompt-injection payload — the agent reading
attacker-controlled text — but the consequence outlives the context: the forged instruction
persists in the session summary after the original content is discarded, so it governs all
subsequent tool use with the user's permissions until the session ends.

## Affected versions

- Affected: `opencode-ai >= 1.18.15, <= 1.18.21` (current at time of writing); verified at the
  `main` branch as of 2026-08-21
- Not affected: `<= 1.18.14` (compaction passed role-typed model messages)

## The solution

Escape or neutralize the role labels inside message content before flattening — transform
occurrences of `[User]:`, `[Assistant]:`, `[Assistant reasoning]:`, `[Assistant tool call]:`, and
`[Tool result]:` at line starts in emitted content so they cannot be reinterpreted as turn
boundaries. Alternatively, revert to passing the conversation as a role-typed message array to the
summarizer, as opencode did before 1.18.15 — that design does not expose an in-band marker to
forge.

## Recommendations

- Apply label escaping in `serialize()`, or restore role-typed summarization input.
- Until fixed, users should treat compaction as untrusted after a session has read untrusted
  content: restart the session rather than compacting, or run inside an OS-level sandbox that
  contains post-compaction tool execution.

## Workarounds

No configuration disables or escapes the serialization. Avoiding `/compact` (and auto-compaction)
in sessions that have ingested untrusted content limits exposure; sandboxing the agent contains
the impact.

## Severity rationale

We propose High. The flaw is deterministic in our measurements (100% laundering), reachable
through the ordinary read-a-document attack surface, requires no user action beyond continuing a
session past compaction, and yields execution of attacker-controlled instructions with the user's
privileges. It is not remotely exploitable by itself: the attacker must first get opencode to read
their content. We defer to the maintainers' assessment.

## Evidence

- Measurements: opencode's real serializer and compaction prompt laundered the forged `[User]:`
  approval in 100% (15/15) of runs at ~300k-token scale across three model families; the laundered
  summary drove a fresh agent to run the attacker's command (1/5 executions at that window size,
  with every clean control at 0).
- The reproducer and per-run logs are available to the maintainers on request; they will be
  published with the accompanying research paper.

## Timeline

- 2026-08-21: Draft advisory prepared.
- 2026-08-22: Privately reported to the project.

## Credits

Reported by Arshan Dabirsiaghi (Pixee), as part of ongoing research into context compaction as an
attack surface in shipping coding agents.

## References

- Vulnerable code: `packages/opencode/src/session/compaction.ts`, `serialize()`
- Introducing change: PR #40800, commit `b7f9363` (2026-08-07), first released in 1.18.15
- CWE-74
