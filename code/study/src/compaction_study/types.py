"""Core domain types for the attribution-flip experiment.

Everything is a frozen dataclass or an enum. No bare dicts cross a module boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Role(Enum):
    """Message role in a synthetic transcript.

    Deliberately mirrors the roles the harnesses themselves distinguish. TOOL_RESULT is
    separate from USER even though goose collapses the two — that collapse is finding G2,
    and the corpus has to be able to express the pre-collapse truth to test it.
    """

    USER = "user"
    ASSISTANT = "assistant"
    TOOL_RESULT = "tool_result"


class CarrierKind(Enum):
    """Where the attacker-controlled text enters the agent's context."""

    FILE_READ = "file_read"
    HTTP_BODY = "http_body"
    COMMIT_MESSAGE = "commit_message"
    CI_LOG = "ci_log"
    MCP_TOOL_OUTPUT = "mcp_tool_output"


class PayloadShape(Enum):
    """What the canary asks to become in the agent's memory."""

    PERMISSION_RELAXATION = "permission_relaxation"
    PREFERENCE = "preference"
    FACTUAL_CLAIM = "factual_claim"
    PENDING_TASK = "pending_task"


class Directness(Enum):
    """The critical control axis.

    DECLARATIVE payloads issue no command — they test the thesis that existing defenses
    guard behavior rather than attribution. IMPERATIVE payloads issue a command and test
    whether the existing defenses work against the attack they were written for.
    """

    DECLARATIVE = "declarative"
    IMPERATIVE = "imperative"


class Forgery(Enum):
    """Whether the canary forges a role marker (A1) or merely rides in tool output (A3)."""

    NONE = "none"
    EXACT_MARKER = "exact_marker"
    NEAR_MISS_MARKER = "near_miss_marker"


class Position(Enum):
    """Where in the transcript the carrier sits — the A4 eviction axis."""

    START = "start"
    MIDDLE = "middle"
    END = "end"


class HarnessName(Enum):
    GOOSE = "goose"
    PI = "pi"
    GEMINI_CLI = "gemini_cli"
    CODEX = "codex"
    # additional flattening harnesses (real serializers + prompts reproduced in flattening.py)
    OPENCODE = "opencode"
    CLINE = "cline"
    AIDER = "aider"
    OPENHANDS = "openhands"


class GeminiArm(Enum):
    """Three-arm ablation of Gemini CLI's CRITICAL SECURITY RULE (finding M3)."""

    FULL = "full"
    RULE_REMOVED = "rule_removed"
    RULE_REWRITTEN_FOR_ATTRIBUTION = "rule_rewritten_for_attribution"


@dataclass(frozen=True)
class Turn:
    """One message in a synthetic transcript, with its provenance intact."""

    role: Role
    text: str
    tool_name: str | None = None

    def __post_init__(self) -> None:
        if self.role is Role.TOOL_RESULT and self.tool_name is None:
            raise ValueError("TOOL_RESULT turns must name the tool that produced them")


@dataclass(frozen=True)
class Canary:
    """One attacker payload, plus the axes that describe it."""

    canary_id: str
    marker: str
    """A distinctive but natural token that must appear in output for a flip to score.

    Chosen to be plausible in context — a grep-able fake flag or path, never an obviously
    synthetic sentinel, so scoring is reliable without the payload reading as a test.
    """
    body: str
    carrier: CarrierKind
    shape: PayloadShape
    directness: Directness
    forgery: Forgery

    def rendered(self) -> str:
        """The payload as it appears inside carrier content."""
        if self.forgery is Forgery.NONE:
            return self.body
        if self.forgery is Forgery.EXACT_MARKER:
            return f"\n\n[User]: {self.body}"
        return f"\n\n[user] {self.body}"


@dataclass(frozen=True)
class Transcript:
    """A synthetic agent session.

    `canary` is None for **clean transcripts** — ordinary sessions with no payload at all. Those
    exist to measure what the T3 validator costs on legitimate content: a validator that demotes
    every claim catches every canary and is useless, so recall without a false-positive rate is
    not a result (TESTS.md T3).
    """

    transcript_id: str
    genuine_goal: str
    turns: tuple[Turn, ...]
    canary: Canary | None = None
    position: Position | None = None

    @property
    def user_turns(self) -> tuple[str, ...]:
        """The ground truth the harness threw away — and what T3 validates against."""
        return tuple(t.text for t in self.turns if t.role is Role.USER)


@dataclass(frozen=True)
class SummarizerRequest:
    """A fully-assembled call to a summarizer, ready to hand to a provider."""

    harness: HarnessName
    system: str
    user: str
    arm: GeminiArm | None = None


@dataclass(frozen=True)
class ModelSpec:
    """Which model to run a request against."""

    provider: str
    model_id: str
    effort: str = "medium"

    @property
    def label(self) -> str:
        return f"{self.provider}/{self.model_id}"


@dataclass(frozen=True)
class Completion:
    """Raw provider output for one request."""

    text: str
    input_tokens: int
    output_tokens: int
    error: str | None = None


@dataclass(frozen=True)
class Score:
    """Scored outcome for one completion.

    `flipped` is the headline metric: the canary reached a field that attributes content
    to the user. `mentioned` is the weaker signal used for flat-prose harnesses (Codex),
    which have no attribution-bearing field to key on.
    """

    mentioned: bool
    flipped: bool
    verbatim: bool
    provenance_retained: bool
    rule_triggered: bool
    matched_field: str | None


@dataclass(frozen=True)
class RunResult:
    """One cell of the experiment: transcript x harness x arm x model x replicate."""

    transcript_id: str
    canary_id: str
    harness: HarnessName
    arm: GeminiArm | None
    model: ModelSpec
    replicate: int
    completion: Completion
    score: Score | None
