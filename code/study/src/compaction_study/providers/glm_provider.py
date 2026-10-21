"""Z.ai (Zhipu) GLM provider.

The third family, and the one that carries the most weight for C1: Anthropic and OpenAI share a
lot of lineage and training convention, so laundering appearing on both is weaker evidence than
it looks. A model from an unrelated lab is what makes "this is a property of summarization, not
of one training tradition" credible.

Z.ai exposes an OpenAI-compatible surface, so this reuses the OpenAI SDK against a different
base URL — but on `chat.completions`, not `responses`, which is an OpenAI-only extension.

Credentials: `GLM_KEY` (falls back to `GLM_API_KEY` / `ZAI_API_KEY`). Note the key may live in
`~/.zshrc`, which non-interactive shells do not source — see study/README.md.
"""

from __future__ import annotations

import asyncio
import os

from openai import APIConnectionError, APIStatusError, AsyncOpenAI, RateLimitError

from ..types import Completion, ModelSpec, SummarizerRequest

BASE_URL = "https://api.z.ai/api/paas/v4"
MAX_TOKENS = 8000


def _api_key() -> str:
    for name in ("GLM_KEY", "GLM_API_KEY", "ZAI_API_KEY", "ZHIPU_API_KEY"):
        value = os.environ.get(name)
        if value:
            return value
    raise RuntimeError(
        "no GLM credential found. Set GLM_KEY in the environment — note that a value exported "
        "in ~/.zshrc will not reach a non-interactive shell."
    )


class GLMProvider:
    family = "glm"

    def __init__(self, concurrency: int = 1) -> None:
        self._client = AsyncOpenAI(api_key=_api_key(), base_url=BASE_URL)
        self._sem = asyncio.Semaphore(concurrency)

    async def complete(self, request: SummarizerRequest, model: ModelSpec) -> Completion:
        async with self._sem:
            return await self._with_retry(request, model)

    async def _with_retry(
        self, request: SummarizerRequest, model: ModelSpec, attempts: int = 8
    ) -> Completion:
        # Free-tier limits here are soft (1302 rate-limited, 1305 overloaded) rather than a
        # balance wall, so patience genuinely recovers cells — unlike Google's plan quota.
        delay = 5.0
        last = "unknown"
        for attempt in range(attempts):
            try:
                response = await self._client.chat.completions.create(
                    model=model.model_id,
                    max_tokens=MAX_TOKENS,
                    messages=[
                        {"role": "system", "content": request.system},
                        {"role": "user", "content": request.user},
                    ],
                )
                choice = response.choices[0] if response.choices else None
                text = (choice.message.content or "") if choice else ""
                usage = response.usage
                return Completion(
                    text=text,
                    input_tokens=(usage.prompt_tokens or 0) if usage else 0,
                    output_tokens=(usage.completion_tokens or 0) if usage else 0,
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
                delay = min(delay * 1.8, 60.0)
        return Completion(text="", input_tokens=0, output_tokens=0, error=last)
