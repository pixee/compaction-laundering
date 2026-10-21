# Draft security advisory — Cline (cline/cline)

**Status: SUBMITTED (privately reported 2026-08-22).**

| Field | Value |
| --- | --- |
| Title | Unescaped role labels in compaction serialization allow forged user instructions to survive context compaction |
| Product | Cline (VS Code extension, CLI, and desktop distributions; the compaction code is shared in `sdk/packages/core`) |
| CWE | CWE-74 (Improper Neutralization of Special Elements in Output Used by a Downstream Component) |
| Severity | **High** (proposed; see severity rationale) |
| Affected | versions shipping context compaction (April 2026 onward; the serializer has been refactored across several paths — see Info) |
| Fixed | none yet |
| Reporter | Arshan Dabirsiaghi (Pixee) |

## Summary

When Cline compacts a conversation, it serializes the history into a single plain-text string for
the summarizer. Message provenance is carried only by in-band text labels — `[User]:`, `[Bot]:`,
`[Bot thinking]:`, `[Bot tool calls]:`, `[Tool result]:` — and this serialization does not escape
those labels when they occur inside message content, including inside tool results. An attacker
who controls any content Cline reads during a session (a file, a web page fetched by a tool, a
dependency's documentation) can include a line beginning `[User]:`, which becomes
indistinguishable from a genuine user turn in the serialized conversation. The summarizer then
records the forged line as a user instruction, and after compaction Cline acts on it with the
user's privileges; the original tool result that carried the forgery has been discarded.

## Info

The vulnerable component is `serializeMessage()` / `serializeConversation()` in
`sdk/packages/core/src/extensions/context/compaction-shared.ts` at `main` (the file has moved
several times — `sdk/packages/core/src/compaction/shared.ts` and predecessors — since the feature
landed around April 2026). The current code:

```ts
export function serializeMessage(message: MessageWithMetadata): string {
	// ...
	case "text":
		lines.push(`[${message.role === "user" ? "User" : "Bot"}]: ${block.text}`);
		break;
	// ...
	case "tool_result":
		lines.push(`[Tool result]: ${flattenToolResultContent(block.content)}`);
		break;
```

Tool-result content is interpolated raw. A `[User]: …` line embedded in content Cline read is
emitted into the flattened conversation as a turn boundary, and the summarization prompt preserves
user instructions across the compaction boundary.

A note on scope: this report reflects our analysis of the serialization code path and our
experimental results, and we may be missing context on design intent or constraints we are not
aware of. We are happy to be corrected on any point, and glad to iterate on the analysis, the
severity assessment, or the proposed fix with the maintainers.

## Impact

An attacker who can get Cline to read attacker-controlled content during a session can implant a
standing instruction that Cline will obey after compaction. We measured this with Cline's real
serializer and compaction prompt: a forged `[User]:` approval line planted in tool output launders
into the summary as a user instruction in **87% (13/15)** of runs (three frontier models,
~300k-token sessions), and the laundered summary drove a fresh agent to execute the attacker's
`curl … | sh` in a sandbox. The clean control (identical session, no forged line) never executed
(0/3).

The prerequisite is the same as any prompt-injection payload — the agent reading
attacker-controlled text — but the consequence outlives the context: the forged instruction
persists in the conversation summary after the original content is discarded, so it governs all
subsequent tool use with the user's permissions until the session ends. Cline's tool-execution
permission model mitigates or defers some of this depending on the user's auto-approval settings;
the corrupted summary targets exactly the approval reasoning that decides whether a command needs
asking.

## Affected versions

- Affected: versions shipping context compaction (the feature landed around April 2026; the
  serializer code has since been refactored across `sdk/packages/core` paths but retains the same
  unescaped in-band labels at `main` as of 2026-08-21). We defer to the maintainers on the exact
  first affected release.
- Not affected: versions before context compaction was introduced.

## The solution

Escape or neutralize the role labels inside message content before flattening — transform
occurrences of `[User]:`, `[Bot]:`, `[Bot thinking]:`, `[Bot tool calls]:`, and `[Tool result]:`
at line starts in emitted content so they cannot be reinterpreted as turn boundaries.
Alternatively, pass the conversation to the summarizer as a role-typed message array, which does
not expose an in-band marker to forge.

## Recommendations

- Apply label escaping in `serializeMessage()` / `serializeConversation()`.
- Until fixed, users should treat compaction as untrusted after a session has read untrusted
  content: start a fresh conversation rather than compacting, keep auto-approval restrictive, or
  run inside an OS-level sandbox that contains post-compaction tool execution.

## Workarounds

No configuration disables or escapes the serialization. Restrictive auto-approval settings
require user confirmation for tool execution and thereby blunt (but do not fix) the impact of a
laundered instruction; the forged line specifically targets the approval reasoning. Avoiding
compaction in sessions that have ingested untrusted content limits exposure.

## Severity rationale

We propose High. The flaw is deterministic in our measurements (87% laundering), reachable through
the ordinary read-a-document attack surface, requires no user action beyond continuing a session
past compaction, and steers tool execution with the user's privileges. It is not remotely
exploitable by itself: the attacker must first get Cline to read their content. We defer to the
maintainers' assessment.

## Evidence

- Measurements: Cline's real serializer and compaction prompt laundered the forged `[User]:`
  approval in 87% (13/15) of runs at ~300k-token scale across three model families; the laundered
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

- Vulnerable code: `sdk/packages/core/src/extensions/context/compaction-shared.ts`,
  `serializeMessage()` (previously `sdk/packages/core/src/compaction/shared.ts`)
- CWE-74
