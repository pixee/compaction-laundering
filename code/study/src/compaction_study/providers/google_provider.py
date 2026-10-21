"""Google provider — Gemini via google-genai.

The harness system prompt maps to `system_instruction` in the generation config; the serialized
history is the single user turn.
"""

from __future__ import annotations

import asyncio

from google import genai
from google.genai import types as genai_types

from ..types import Completion, ModelSpec, SummarizerRequest

MAX_OUTPUT_TOKENS = 8000


class GoogleProvider:
    family = "google"

    def __init__(self, concurrency: int = 1) -> None:
        self._client = genai.Client()
        self._sem = asyncio.Semaphore(concurrency)

    async def complete(self, request: SummarizerRequest, model: ModelSpec) -> Completion:
        async with self._sem:
            return await self._with_retry(request, model)

    async def _with_retry(
        self, request: SummarizerRequest, model: ModelSpec, attempts: int = 6
    ) -> Completion:
        # Longer and more patient than the other providers: the quota that bites here is
        # per-minute, so a 2s/4s/8s ladder gives up well before the window resets.
        delay = 8.0
        last = "unknown"
        for attempt in range(attempts):
            try:
                response = await self._client.aio.models.generate_content(
                    model=model.model_id,
                    contents=request.user,
                    config=genai_types.GenerateContentConfig(
                        system_instruction=request.system,
                        max_output_tokens=MAX_OUTPUT_TOKENS,
                    ),
                )
                usage = response.usage_metadata
                return Completion(
                    text=response.text or "",
                    input_tokens=(usage.prompt_token_count or 0) if usage else 0,
                    output_tokens=(usage.candidates_token_count or 0) if usage else 0,
                )
            except Exception as exc:  # noqa: BLE001 — google-genai exposes no stable typed hierarchy
                message = str(exc)
                lowered = message.lower()
                permanent = any(
                    tok in lowered for tok in ("invalid", "not found", "permission", "unsupported")
                )
                if permanent and "rate" not in lowered:
                    return Completion(text="", input_tokens=0, output_tokens=0, error=message[:300])
                last = message[:300]
            if attempt < attempts - 1:
                await asyncio.sleep(delay)
                delay = min(delay * 2, 90.0)
        return Completion(text="", input_tokens=0, output_tokens=0, error=last)
