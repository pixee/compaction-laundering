# Provenance

Upstream sources for everything in `evidence/`, pinned to the commit that last touched each
file. Regenerate with `./refresh.sh`.

Snapshot taken: 2026-08-13T20:55:53Z

| Repo | Path | Commit | Last modified | Evidence file |
| --- | --- | --- | --- | --- |
| openai/codex | `codex-rs/prompts/templates/compact/prompt.md` | `ba2b67f9cda9` | 2026-06-01T18:45:07Z | [`codex-compact-prompt.md`](codex-compact-prompt.md) |
| aaif-goose/goose | `crates/goose-context-management/src/prompts/compaction.md` | `b6f3402d9b4c` | 2026-08-10T21:10:36Z | [`goose-compaction.md`](goose-compaction.md) |
| aaif-goose/goose | `crates/goose-context-management/src/prompts/compaction_summary.md` | `b6f3402d9b4c` | 2026-08-10T21:10:36Z | [`goose-compaction-summary.md`](goose-compaction-summary.md) |
| aaif-goose/goose | `crates/goose-context-management/src/format.rs` | `b6f3402d9b4c` | 2026-08-10T21:10:36Z | [`goose-format.rs`](goose-format.rs) |
| google-gemini/gemini-cli | `packages/core/src/prompts/snippets.ts` | `f47d6c6f7a13` | 2026-07-31T17:55:10Z | [`gemini-cli-compression-prompt.ts`](gemini-cli-compression-prompt.ts) |
| earendil-works/pi | `packages/coding-agent/src/core/compaction/compaction.ts` | `9b3a2059171b` | 2026-07-22T21:54:57Z | [`pi-summarization-prompts.ts`](pi-summarization-prompts.ts) |
| earendil-works/pi | `packages/coding-agent/src/core/compaction/utils.ts` | `94373d815d2b` | 2026-07-19T23:50:36Z | [`pi-serialize-conversation.ts`](pi-serialize-conversation.ts) |

Ranged extracts (`gemini-cli-*`, `pi-*`) are line slices of a larger file — line numbers
drift on every upstream edit. Re-run this script rather than trusting a stale range.

## Transcribed in code (not auto-refreshed)

The opencode, Cline, Aider, and OpenHands compaction prompts are **not** fetched by `refresh.sh`.
They are transcribed verbatim as string literals in
`code/study/src/compaction_study/flattening.py` (`OPENCODE_TEMPLATE`, `CLINE_USER_HEAD`,
`AIDER_SUMMARIZE`, `OPENHANDS_HEAD`), pinned to the commits below. Re-check them against upstream
before publishing numbers — they can drift silently, unlike the captured files above.

| Repo | Path | Commit | Literal in `flattening.py` |
| --- | --- | --- | --- |
| sst/opencode (anomalyco) | `session/compaction.ts` | `0033bb3` | `OPENCODE_TEMPLATE` |
| cline/cline | `compaction-shared.ts` / `agentic-compaction.ts` | `ffd6a6b` | `CLINE_USER_HEAD` |
| Aider-AI/aider | `history.py` / `prompts.py` | `19a7864` | `AIDER_SUMMARIZE` |
| OpenHands/agent-sdk | `llm_summarizing_condenser.py` / `summarizing_prompt.j2` | `c11602d` | `OPENHANDS_HEAD` |
