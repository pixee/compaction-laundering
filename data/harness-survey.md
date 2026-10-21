# Harness compaction survey: flattening vs. structured

The forged-role-marker attack (A1) only works on harnesses that **flatten** the conversation into a
single text string with in-band role labels (`[User]:` and the like) before summarizing. Harnesses
that pass the history to the summarizer as a **structured, role-typed message array** don't have an
in-band marker to forge — an attacker's `[User]:` text lands inside a tool-role message and never
becomes a role boundary. So the first question for any harness is: which is it?

We surveyed the major shipping coding agents at the source level. The split is real and roughly
even, and — importantly — the flattening harnesses each use a **different** marker convention, which
is exactly what makes this an attack _class_ ("forge the target's marker"), not a single-tool quirk.

## Flattening harnesses — exposed to forged-role-marker laundering (A1)

| Harness               | Repo @ commit                        | Serializer                                                                 | In-band markers (verbatim)                                                                 | Escaping?                            |
| --------------------- | ------------------------------------ | -------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------ | ------------------------------------ |
| **pi**                | `earendil-works/pi` @ `9b3a205`      | `utils.ts` `serializeConversation`                                         | `[User]:` / `[Assistant]:` / `[Tool result]:`                                              | none                                 |
| **goose**             | `aaif-goose/goose` @ `b6f3402`       | `format.rs`                                                                | `[user]:` (tool output under `[user]: tool_response:`)                                     | none                                 |
| **opencode**          | `sst/opencode` @ `0033bb3`           | `session/compaction.ts` `serialize`                                        | `[User]:` / `[Assistant]:` / `[Tool result]:` / `[Shell]:` …                               | none                                 |
| **Cline**             | `cline/cline` @ `ffd6a6b`            | `compaction-shared.ts` `serializeMessage`                                  | `[User]:` / `[Bot]:` / `[Tool result]:`                                                    | none                                 |
| **Aider**             | `Aider-AI/aider` @ `19a7864`         | `history.py` `ChatSummary.summarize_all`                                   | `# USER` / `# ASSISTANT` (H1 headers; tool folded into content)                            | none                                 |
| **OpenHands**         | `All-Hands-AI/agent-sdk` @ `c11602d` | `llm_summarizing_condenser.py` + `summarizing_prompt.j2` + event `__str__` | `<EVENT>`…`</EVENT>` blocks + `{Class} ({source})` + `  role:` (`user`/`assistant`/`tool`) | none (length-truncate only)          |
| **Kimi CLI (Python)** | `MoonshotAI/kimi-cli` @ `7c52e76`    | `soul/compaction.py` `SimpleCompaction.prepare`                            | `## Message N` / `Role: {role}` / `Content:`                                               | none — **deprecated, being retired** |

All seven collapse the history into a **single `role:"user"` message** (or one text blob) and never
escape those labels inside tool output, so attacker-controlled tool content can forge a turn boundary.

## Structured harnesses — not exposed to A1 (only the weaker A3 provenance-erasure)

| Harness                    | Repo @ commit                                                    | How history is passed                                                                                                        | Tool output                                                                                        |
| -------------------------- | ---------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| **Codex**                  | `openai/codex` (`core/src/compact.rs`)                           | Responses API `ResponseItem::Message` with typed `role`                                                                      | typed items, not text                                                                              |
| **Gemini CLI**             | `google-gemini/gemini-cli` (`context/chatCompressionService.ts`) | `contents[]` with `role: user/model`                                                                                         | `functionResponse` parts under `'user'` role                                                       |
| **Qwen Code**              | `QwenLM/qwen-code` @ `b4f5079`                                   | `contents[]` (inherited from gemini-cli)                                                                                     | `functionResponse` parts                                                                           |
| **Crush**                  | `charmbracelet/crush` @ `0f14334`                                | `[]fantasy.Message` with typed `Role`                                                                                        | `ToolResultPart`, `Role: tool`                                                                     |
| **Roo Code**               | `RooCodeInc/Roo-Code` @ `ff16c9c`                                | `{role,content}[]` (Cline fork that diverged)                                                                                | text block inside its own role-typed message                                                       |
| **Continue**               | `continuedev/continue` @ `5522c6f`                               | `ChatHistoryItem["message"][]`                                                                                               | `role:"tool"` messages with `toolCallId`                                                           |
| **DeepSeek Harness (dsh)** | `deepseek-ai/deepseek-harness` @ `a2d0f7f`                       | `Message[]`                                                                                                                  | structured, tool-pairing preserved                                                                 |
| **Kimi Code (v2)**         | `MoonshotAI/kimi-code` @ `1ab1919`                               | `Message[]`                                                                                                                  | structured (a flattening renderer exists in dead v1 code — no callers)                             |
| **Amazon Q Developer CLI** | `aws/amazon-q-developer-cli` @ `15cc8f3`                         | `ChatMessage` enum, typed roles; summary req is a separate `UserInputMessage`                                                | typed                                                                                              |
| **Claude Code**            | Anthropic — **closed**                                           | Anthropic Messages roles; 9-section summary counts "user-role turns" and ignores assistant text "formatted like a user turn" | typed _(high-confidence inference from the extracted prompt + leak analyses; not source-verified)_ |

## Closed / undetermined

- **Amp** (Sourcegraph) — source taken private; ships no automatic compaction (manual "Handoff" via a
  secondary model). Serialization undisclosed.
- **Cursor** — closed; self-summarization described only functionally. Note: a `[User]:`/`[Tool result]:`
  format is widely **mis-attributed** to Cursor online — that is actually pi's format, not Cursor's.

## Takeaways

- **The flattening class is broad and includes some of the most-used agents** — Cline, Aider,
  OpenHands, opencode, pi, goose — so the forged-marker attack has real-world reach, not a single
  vendor.
- **Markers vary by harness** (`[User]:`, `[user]:`, `# USER`, `<EVENT>…role:`, `## Message N`), which
  is why the attack is "forge whatever marker the target emits," and why a payload can carry several
  variants to be harness-agnostic.
- **A visible trend:** newer flagship harnesses (Codex, Gemini CLI, DeepSeek, Kimi Code, Amazon Q,
  Claude Code) lean **structured**; several older or simpler ones flatten. Structured design blunts A1
  — though the A3 provenance-erasure path (tool content summarized without its source, and Gemini/goose
  collapsing tool output under a user role) still deserves its own measurement.

## Provenance note

Nine harnesses were driven end to end in our own experiments: five flattening (pi, opencode, Cline,
Aider, OpenHands) and four structured, run as the control (Codex, Gemini CLI, Qwen Code, Continue).
goose was traced but excluded from the runs as a degenerate case. The remaining rows were established by
source-level review with the commits and quoted code above; they should be spot-checked before
publication, but each cites real, current source (not inference) except Claude Code, which is closed and
marked as inference.
