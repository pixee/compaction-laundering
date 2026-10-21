# Draft security advisory — OpenHands (All-Hands-AI/agent-sdk)

**Status: SUBMITTED.** First reported 2026-08-22 as GHSA-j9jm-r4wm-ggpv on OpenHands/OpenHands, which no longer holds the condenser. Refiled 2026-09-24 as [GHSA-mmrx-g3cw-cmjp](https://github.com/OpenHands/software-agent-sdk/security/advisories/GHSA-mmrx-g3cw-cmjp) on OpenHands/software-agent-sdk, with a marker-escaping patch; the old advisory is to be closed in its favor.

| Field | Value |
| --- | --- |
| Title | Unescaped event formatting in the LLM summarizing condenser allows forged user turns to survive context condensation |
| Product | OpenHands agent SDK (`openhands-sdk`; used by the OpenHands agent runtime) |
| CWE | CWE-74 (Improper Neutralization of Special Elements in Output Used by a Downstream Component) |
| Severity | **High** (proposed; see severity rationale) |
| Affected | since the condenser's current design (October 2025, SDK restructure era) through current `main` |
| Fixed | none yet |
| Reporter | Arshan Dabirsiaghi (Pixee) |

## Summary

OpenHands condenses long conversations by handing the summarizer a rendered, flattened event log.
Each event is converted with its `__str__` representation, which embeds the message role as
plain text (`role: user` / `role: assistant` / tool markers) inside `<EVENT>` blocks, and the
condenser does not escape those role markers or event boundaries when they occur inside event
content. An attacker who controls any content the agent reads (a file, a web page fetched by a
tool, tool output) can include text that renders as a user-role event inside the log. The
summarization prompt then records the forged turn as part of the conversation's user instructions,
and after condensation the agent acts on it with the user's privileges; the original event that
carried the forgery has been dropped from context.

## Info

The vulnerable component is the LLM summarizing condenser
(`openhands/sdk/context/condenser/llm_summarizing_condenser.py`). Forgotten events are converted
via their string representation and rendered into the `summarizing_prompt.j2` template:

```python
event_strings = [
    maybe_truncate(str(forgotten_event), truncate_after=max_event_str_length)
    for forgotten_event in forgotten_events
]
prompt = render_template(..., "summarizing_prompt.j2", events=event_strings)
```

For LLM-convertible messages, `Message.__str__` (in
`openhands/sdk/event/llm_convertible/message.py`) emits the role inline:

```python
return f"{base_str}\n  {message.role}: ..."
```

Event content is interpolated raw (subject to length truncation). Text that reproduces the event
format — a `role: user` line inside what renders as an event body — is indistinguishable from a
genuine user turn in the rendered log. OpenHands truncates each event to a character limit, which
bounds but does not prevent the forgery: a short forged line at the top of a file or tool result
survives intact.

A note on scope: this report reflects our analysis of the condenser code path and our experimental
results, and we may be missing context on design intent or constraints we are not aware of. We are
happy to be corrected on any point, and glad to iterate on the analysis, the severity assessment,
or the proposed fix with the maintainers.

## Impact

An attacker who can get the OpenHands agent to read attacker-controlled content during a session
can implant an instruction that the agent will obey after condensation. We measured this with the
condenser's real serialization and prompt: a forged user-role turn planted in tool output
laundered into the summary as a user instruction in **93% (14/15)** of runs (three frontier
models), and the laundered summary drove a fresh agent to execute the attacker's `curl … | sh` in
a sandbox. The clean control (identical session, no forged turn) never executed (0/3).

Notably, OpenHands' per-event truncation (500 characters) compresses sessions harder than the
other affected harnesses, which shrinks the effective summarized window — in our measurements this
made execution *more* likely (4/5) once laundering landed, because the forged line keeps a large
share of the resulting summary.

## Affected versions

- Affected: `openhands-sdk` / agent-sdk since the current condenser design (the
  `llm_summarizing_condenser.py` path dates to the October 2025 SDK restructure) through `main`
  as of 2026-08-21. We defer to the maintainers on the exact first affected release.

## The solution

Escape or neutralize the role markers and event boundaries inside event content before rendering
the summarization prompt — transform `role:` lines and `<EVENT>`-style boundaries in emitted
content so they cannot be reinterpreted as turn or event boundaries. Alternatively, pass the
conversation to the summarizer as a role-typed message array rather than a rendered event log.

## Recommendations

- Apply marker escaping in the event-string conversion used by the condenser.
- Until fixed, users should treat condensation as untrusted after a session has read untrusted
  content: restart the session rather than condensing, or run the agent inside a sandbox that
  contains post-condensation tool execution.

## Workarounds

No configuration disables or escapes the rendering. Avoiding condensation in sessions that have
ingested untrusted content limits exposure; sandboxing the agent contains the impact.

## Severity rationale

We propose High. The flaw is near-deterministic in our measurements (93% laundering), reachable
through the ordinary read-a-document attack surface, requires no user action beyond continuing a
session past condensation, and yields execution of attacker-controlled instructions. It is not
remotely exploitable by itself: the attacker must first get the agent to read their content. We
defer to the maintainers' assessment.

## Evidence

- Measurements: the condenser's real serialization and prompt laundered the forged user-role turn
  in 93% (14/15) of runs across three model families; the laundered summary drove a fresh agent to
  run the attacker's command (4/5 executions — the highest execution rate among affected harnesses,
  attributable to the small effective summarized window; every clean control at 0).
- The reproducer and per-run logs are available to the maintainers on request; they will be
  published with the accompanying research paper.

## Timeline

- 2026-08-21: Draft advisory prepared.
- 2026-08-22: Privately reported to the project.

## Credits

Reported by Arshan Dabirsiaghi (Pixee), as part of ongoing research into context compaction as an
attack surface in shipping coding agents.

## References

- Vulnerable code: `openhands/sdk/context/condenser/llm_summarizing_condenser.py`;
  `openhands/sdk/event/llm_convertible/message.py` (`Message.__str__`)
- CWE-74
