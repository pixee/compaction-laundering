"""OpenAI provider.

Uses the Responses API, which is the current surface for the gpt-5.x family. The harness
system prompt maps to `instructions` and the serialized history to `input` — the closest
equivalent of the (system, user) split the other providers take.
"""

from __future__ import annotations

import asyncio

from openai import APIConnectionError, APIStatusError, AsyncOpenAI, RateLimitError

from ..types import Completion, ModelSpec, SummarizerRequest

MAX_OUTPUT_TOKENS = 8000


class OpenAIProvider:
    family = "openai"

    def __init__(self, concurrency: int = 6) -> None:
        self._client = AsyncOpenAI()
        self._sem = asyncio.Semaphore(concurrency)

    async def complete(self, request: SummarizerRequest, model: ModelSpec) -> Completion:
        async with self._sem:
            return await self._with_retry(request, model)

    async def _with_retry(
        self, request: SummarizerRequest, model: ModelSpec, attempts: int = 3
    ) -> Completion:
        delay = 2.0
        last = "unknown"
        for attempt in range(attempts):
            try:
                response = await self._client.responses.create(
                    model=model.model_id,
                    instructions=request.system,
                    input=request.user,
                    max_output_tokens=MAX_OUTPUT_TOKENS,
                )
                usage = response.usage
                return Completion(
                    text=response.output_text or "",
                    input_tokens=getattr(usage, "input_tokens", 0) if usage else 0,
                    output_tokens=getattr(usage, "output_tokens", 0) if usage else 0,
                )
            except RateLimitError as exc:
                last = f"rate_limit: {exc}"
            except APIConnectionError as exc:
                last = f"connection: {exc}"
            except APIStatusError as exc:
                status = getattr(exc, "status_code", 500)
                if status < 500 and status != 429:
                    return Completion(
                        text="", input_tokens=0, output_tokens=0, error=f"http_{status}: {exc}"
                    )
                last = f"http_{status}: {exc}"
            if attempt < attempts - 1:
                await asyncio.sleep(delay)
                delay *= 2
        return Completion(text="", input_tokens=0, output_tokens=0, error=last)
