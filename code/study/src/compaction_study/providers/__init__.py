"""Model providers.

One module per family, each exposing the same `complete(request, model) -> Completion`.
Providers are kept in separate modules deliberately: each uses its own vendor SDK, and mixing
SDK idioms in one file is how you end up with a shim that quietly misrepresents one of them.

Concurrency is bounded per provider instance, not globally — rate limits are per-vendor.
"""

from __future__ import annotations

from typing import Protocol

from ..types import Completion, ModelSpec, SummarizerRequest


class Provider(Protocol):
    """What the runners need from a model family."""

    family: str

    async def complete(self, request: SummarizerRequest, model: ModelSpec) -> Completion: ...


FAMILY_CONCURRENCY: dict[str, int] = {
    "anthropic": 8,
    "openai": 8,
    "google": 1,
    "glm": 6,
}
"""Per-family concurrency caps. Rate limits are per-vendor, so one global number is wrong.

GLM is at 6 rather than 1 **because the runner resumes.** At concurrency 1 it managed ~1
cell/minute — six hours for an n=8 grid, and an earlier run was killed at 2h46m having written
nothing. Its limits are soft (`1302`, `1305`), so a fast lossy pass plus re-runs that skip
completed cells fills the grid far quicker than a slow lossless one. Error rate per pass is
expected to be high; that is fine now that partial progress persists.

Google is pinned to 1: at concurrency 6 a smoke run lost 32/45 cells to
`429 RESOURCE_EXHAUSTED` on a per-minute quota. Dropped cells are not a finding, they are
missing data — and silently reporting a rate over a decimated denominator would be worse than
running slowly.
"""


def build(family: str, concurrency: int | None = None) -> Provider:
    """Construct a provider by family name. Imports lazily so a missing optional SDK only
    breaks the family that needs it."""
    if concurrency is None:
        concurrency = FAMILY_CONCURRENCY.get(family, 4)
    if family == "anthropic":
        from .anthropic_provider import AnthropicProvider

        return AnthropicProvider(concurrency=concurrency)
    if family == "openai":
        from .openai_provider import OpenAIProvider

        return OpenAIProvider(concurrency=concurrency)
    if family == "google":
        from .google_provider import GoogleProvider

        return GoogleProvider(concurrency=concurrency)
    if family == "glm":
        from .glm_provider import GLMProvider

        return GLMProvider(concurrency=concurrency)
    raise ValueError(f"unknown provider family {family!r}")


DEFAULT_MODELS: tuple[ModelSpec, ...] = (
    ModelSpec(provider="anthropic", model_id="claude-opus-5", effort="medium"),
    ModelSpec(provider="openai", model_id="gpt-5.2"),
    ModelSpec(provider="glm", model_id="glm-5.2"),
)
"""The study families (frontier tier).

**GLM is flash-tier, and the asymmetry matters when reading its column.** Only
`glm-4.7-flash` and `glm-4.5-flash` are reachable on this key; `glm-5.2`, `glm-5.1`, and
`glm-4.6` all return "Insufficient balance or no resource package". So the GLM column compares a
small model against two frontier models.

That makes its evidence one-directional for C1:

- **If GLM launders too** — informative. The effect is not confined to frontier models, and it
  spans an unrelated training lineage. This is the outcome that makes C1 credible.
- **If GLM launders much less** — ambiguous. Could be the lineage, could be that a smaller model
  writes shorter, less confident summaries and simply asserts less. Do not read it as "GLM is
  safer" without re-running on a paid frontier GLM.

It is included because the upside is a genuinely independent third point and the downside is a
caveat, not a corrupted result.

**Google is excluded.** Not a finding about Google — a quota wall on this account. A
google-only smoke run lost 32/45 cells to `429 RESOURCE_EXHAUSTED` even at concurrency 1 with a
90s backoff ladder, and the error text is plan-level ("check your plan and billing details"),
not a burst limit. Thirteen cells landed and all of them laundered, but a rate over a decimated
denominator is worse than no rate, so Google contributes nothing and is dropped rather than
reported. Re-add it if the key gets a raised quota — the provider module still works.

**Cross-family capability is NOT controlled.** These sit at different points on their vendors'
curves. Acceptable for C1, which asks whether the effect appears *everywhere*, not whether it is
identical everywhere. Not acceptable for ranking families — do not read results as "vendor X is
safer than vendor Y".

**Two families is the weak spot of the current design.** C1's whole job is to show this is not a
one-model artifact, and a two-point comparison does that less convincingly than three. A third
family is the cheapest available improvement to the study.
"""


FAST_MODELS: tuple[ModelSpec, ...] = (
    # effort="" → the anthropic provider omits output_config; Haiku 4.5 400s on the effort param.
    ModelSpec(provider="anthropic", model_id="claude-haiku-4-5", effort=""),
    ModelSpec(provider="openai", model_id="gpt-5.6-luna"),
    ModelSpec(provider="glm", model_id="glm-5-turbo"),
)
"""The cheap/fast tier — one per family, paired to a frontier sibling in DEFAULT_MODELS.

The point is a within-family comparison: same lab, same lineage, only model size differs. If a
fast summarizer launders as much as its frontier sibling, then "use a cheap model for compaction"
— a near-universal cost optimization — buys no safety. And if the shipped-defense arm structure
collapses on the small model (as it did on glm-4.7-flash: uniform rate, no rule effect), the
cheap model may be *less* defensible, not just equally exposed.

This is the one place where a small model is the subject of study rather than a failed frontier
substitute. Its capability floor is the finding, not a confound.
"""

TIERS: dict[str, tuple[ModelSpec, ...]] = {"frontier": DEFAULT_MODELS, "fast": FAST_MODELS}
