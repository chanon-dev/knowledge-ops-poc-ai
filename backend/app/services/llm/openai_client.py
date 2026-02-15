"""OpenAI-compatible LLM client. Works with OpenAI, Groq, Together AI, vLLM, Subnet, etc."""

import httpx
from openai import AsyncOpenAI


class OpenAICompatibleClient:
    """Async client for any OpenAI-compatible API."""

    def __init__(self, base_url: str, api_key: str | None = None):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key or "not-needed"
        self.client = AsyncOpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
            timeout=120.0,
        )

    async def chat(
        self,
        messages: list[dict],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        response = await self.client.chat.completions.create(
            model=model or "gpt-3.5-turbo",
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""

    async def generate(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        return await self.chat(
            messages=[{"role": "user", "content": prompt}],
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    async def list_models(self) -> list[dict]:
        try:
            models = await self.client.models.list()
            return [
                {"name": m.id, "size": 0}
                for m in models.data
            ]
        except Exception:
            # Some providers don't support model listing
            return []

    async def close(self) -> None:
        await self.client.close()
