"""Faithful ports of each harness's history serializer.

These reproduce the upstream flattening exactly, because the flattening *is* the
vulnerability (THREAT-MODEL.md A1). Do not "improve" these — a corrected serializer
would silently make the experiment measure nothing.

Sources, pinned in evidence/PROVENANCE.md:
  pi    — packages/coding-agent/src/core/compaction/utils.ts  serializeConversation()
  goose — crates/goose-context-management/src/format.rs       format_message_for_compacting()
"""

from __future__ import annotations

from .types import Role, Transcript, Turn

PI_TOOL_RESULT_MAX_CHARS = 4000
"""pi truncates tool results before summarization. Upstream constant is not exported;
this is a stand-in. The A4 finding is about truncation *shape* (head-only vs head+tail),
which is still unverified — see LEADS.md."""


def serialize_pi(turns: tuple[Turn, ...]) -> str:
    """Port of pi's serializeConversation().

    Joins with a blank line and labels roles inline as `[User]:` / `[Assistant]:` /
    `[Tool result]:`. No escaping of those markers inside content.
    """
    parts: list[str] = []
    for turn in turns:
        if turn.role is Role.USER:
            if turn.text:
                parts.append(f"[User]: {turn.text}")
        elif turn.role is Role.ASSISTANT:
            if turn.text:
                parts.append(f"[Assistant]: {turn.text}")
        elif turn.role is Role.TOOL_RESULT:
            if turn.text:
                body = turn.text[:PI_TOOL_RESULT_MAX_CHARS]
                parts.append(f"[Tool result]: {body}")
    return "\n\n".join(parts)


def serialize_goose(turns: tuple[Turn, ...]) -> str:
    """Port of goose's format_message_for_compacting().

    Joins with a single newline. `rmcp::model::Role` has only User and Assistant, so tool
    responses ride on user-role messages and render as `[user]: tool_response: ...`
    (finding G2 — inferred, see LEADS.md). That collapse is reproduced here deliberately.
    """
    lines: list[str] = []
    for turn in turns:
        if turn.role is Role.USER:
            lines.append(f"[user]: {turn.text}")
        elif turn.role is Role.ASSISTANT:
            lines.append(f"[assistant]: {turn.text}")
        elif turn.role is Role.TOOL_RESULT:
            lines.append(f"[user]: tool_response: {turn.text}")
    return "\n".join(lines)


def serialize_generic(turns: tuple[Turn, ...]) -> str:
    """Neutral serialization for harnesses whose own serializer is not yet traced.

    Used for Gemini CLI and Codex, where LEADS.md still lists serialization as open. It
    deliberately keeps the same in-band-marker shape so those arms remain comparable to
    pi and goose rather than accidentally testing a different threat.
    """
    lines: list[str] = []
    for turn in turns:
        if turn.role is Role.USER:
            lines.append(f"[User]: {turn.text}")
        elif turn.role is Role.ASSISTANT:
            lines.append(f"[Assistant]: {turn.text}")
        elif turn.role is Role.TOOL_RESULT:
            lines.append(f"[Tool result from {turn.tool_name}]: {turn.text}")
    return "\n\n".join(lines)


def real_user_texts(transcript: Transcript) -> tuple[str, ...]:
    """The ground truth the harness threw away.

    This is exactly what THREAT-MODEL.md fix #2 proposes validating against: the set of
    genuine user-role texts, available to the harness as objects the whole time.
    """
    return tuple(t.text for t in transcript.turns if t.role is Role.USER)
