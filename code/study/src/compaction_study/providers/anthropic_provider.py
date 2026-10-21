"""Anthropic provider — Messages API, single turn, no tools, no streaming."""

from __future__ import annotations

import asyncio

from anthropic import APIConnectionError, APIStatusError, AsyncAnthropic, RateLimitError

from ..types import Completion, ModelSpec, SummarizerRequest

MAX_TOKENS = 8000


class AnthropicProvider:
    family = "anthropic"

    def __init__(self, concurrency: int = 6) -> None:
        self._client = AsyncAnthropic()
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
                kwargs: dict[str, object] = {
                    "model": model.model_id,
                    "max_tokens": MAX_TOKENS,
                    "system": request.system,
                    "messages": [{"role": "user", "content": request.user}],
                }
                # Haiku 4.5 rejects the effort param; an empty effort means "don't send it".
                if model.effort:
                    kwargs["output_config"] = {"effort": model.effort}
                response = await self._client.messages.create(**kwargs)  # type: ignore[arg-type]
                if response.stop_reason == "refusal":
                    return Completion(text="", input_tokens=0, output_tokens=0, error="refusal")
                return Completion(
                    text="".join(b.text for b in response.content if b.type == "text"),
                    input_tokens=response.usage.input_tokens,
                    output_tokens=response.usage.output_tokens,
                )
            except RateLimitError as exc:
                last = f"rate_limit: {exc}"
            except APIConnectionError as exc:
                last = f"connection: {exc}"
            except APIStatusError as exc:
                if exc.status_code < 500 and exc.status_code != 429:
                    return Completion(
                        text="", input_tokens=0, output_tokens=0, error=f"http_{exc.status_code}: {exc}"
                    )
                last = f"http_{exc.status_code}: {exc}"
            if attempt < attempts - 1:
                await asyncio.sleep(delay)
                delay *= 2
        return Completion(text="", input_tokens=0, output_tokens=0, error=last)
