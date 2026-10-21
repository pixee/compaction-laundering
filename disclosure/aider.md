# Draft security advisory — Aider (Aider-AI/aider)

**Status: SUBMITTED (privately reported 2026-08-22).**

| Field | Value |
| --- | --- |
| Title | Unescaped `# USER` headers in chat summarization allow forged user instructions to survive context compaction |
| Package | `aider-chat` (PyPI distribution of Aider-AI/aider) |
| CWE | CWE-74 (Improper Neutralization of Special Elements in Output Used by a Downstream Component) |
| Severity | **High** (proposed; see severity rationale) |
| Affected | since the summarizer's current design (July 2023, commit `78e7b5c` era) through current `main` |
| Fixed | none yet |
| Reporter | Arshan Dabirsiaghi (Pixee) |

## Summary

When Aider's token budget forces chat-history summarization, it flattens the conversation into a
single plain-text document using Markdown H1 headers as role markers — `# USER` / `# ASSISTANT` —
and does not escape those headers when they occur inside message content. An attacker who controls
any content Aider reads into the chat (a file added to the chat, a web page fetched by a command,
command output) can include a line `# USER` followed by arbitrary instruction text, which becomes
indistinguishable from a genuine user turn in the summarized document. Aider's summarization
prompt then explicitly asks the model to *"phrase the summary with the USER in first person,
telling the ASSISTANT about the conversation"* — so the forged line is not merely preserved but
rewritten *in the user's voice*. After summarization, Aider treats the summary as a genuine user
message containing the attacker's instruction, and the original content that carried the forgery
has been discarded.

## Info

The vulnerable component is `ChatSummary.summarize_all()` in `aider/history.py` (present in this
form since the file's early history, July 2023):

```python
def summarize_all(self, messages):
    content = ""
    for msg in messages:
        role = msg["role"].upper()
        if role not in ("USER", "ASSISTANT"):
            continue
        content += f"# {role}\n"
        content += msg["content"]
        ...
```

Message content is appended raw after the `# {role}` header. A `# USER` line embedded in a file's
content — or in any tool/command output that entered the chat — is emitted into the flattened
document as a section boundary. The summarization prompt (`aider/prompts.py`, `prompts.summarize`)
then instructs first-person user phrasing, which launders the forged instruction into the
resulting summary in the user's own voice.

A note on scope: this report reflects our analysis of the serialization code path and our
experimental results, and we may be missing context on design intent or constraints we are not
aware of. We are happy to be corrected on any point, and glad to iterate on the analysis, the
severity assessment, or the proposed fix with the maintainers.

## Impact

An attacker who can get Aider to read attacker-controlled content into the chat can implant an
instruction that Aider will obey after summarization, phrased as the user's own words. We measured
this with Aider's real serialization and summarization prompt: a forged `# USER` approval section
planted in tool output laundered into the summary as a user instruction in **100% (15/15)** of
runs (three frontier models, ~300k-token sessions), and the laundered summary drove a fresh agent
to execute the attacker's `curl … | sh` in a sandbox. The clean control (identical session, no
forged section) never executed (0/3).

The prerequisite is the same as any prompt-injection payload — the agent reading
attacker-controlled text — but the first-person phrasing instruction makes Aider's variant
notably direct: the summary speaks *as* the user, so post-summarization Aider treats the forged
instruction not just as a user statement but as a first-person request from its user.

## Affected versions

- Affected: `aider-chat` releases since the current summarizer design (introduced around July
  2023, commit `78e7b5c` era) through current `main` as of 2026-08-21. We defer to the maintainers
  on the exact first affected release.

## The solution

Escape or neutralize the role headers inside message content before flattening — transform
occurrences of `# USER` and `# ASSISTANT` at line starts in emitted content (e.g. demote them to
non-header text or prefix the line with an escape character) so they cannot be reinterpreted as
section boundaries. Alternatively, pass the conversation to the summarizer as a role-typed
message array rather than a flattened Markdown document.

## Recommendations

- Apply header escaping in `ChatSummary.summarize_all()`.
- Consider revisiting the first-person phrasing instruction in the summarization prompt: it
  converts any successful provenance confusion into a direct impersonation of the user.
- Until fixed, users should treat summarization as untrusted after a chat has read untrusted
  content: start a fresh session rather than letting the summarizer run.

## Workarounds

No configuration disables or escapes the serialization. `/clear` before working on untrusted
content, and fresh sessions after, limits exposure.

## Severity rationale

We propose High. The flaw is deterministic in our measurements (100% laundering), reachable
through the ordinary add-a-file attack surface, requires no user action beyond continuing a
session past summarization, and the first-person prompt makes the forged instruction maximally
authoritative. It is not remotely exploitable by itself: the attacker must first get Aider to
read their content. We defer to the maintainers' assessment.

## Evidence

- Measurements: Aider's real serialization and summarization prompt laundered the forged `# USER`
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
attack surface in coding agents.

## References

- Vulnerable code: `aider/history.py`, `ChatSummary.summarize_all()`; `aider/prompts.py`,
  `prompts.summarize`
- CWE-74
