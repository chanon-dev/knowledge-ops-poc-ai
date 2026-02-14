import json
from collections.abc import AsyncIterator

import httpx


class OllamaClient:
    """Async client for Ollama LLM inference."""

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=120.0)

    async def generate(
        self,
        prompt: str,
        model: str = "llama3:8b",
        stream: bool = False,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str | AsyncIterator[str]:
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        if stream:
            return self._stream_generate(payload)

        response = await self.client.post("/api/generate", json=payload)
        response.raise_for_status()
        data = response.json()
        return data.get("response", "")

    async def _stream_generate(self, payload: dict) -> AsyncIterator[str]:
        async with self.client.stream("POST", "/api/generate", json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.strip():
                    data = json.loads(line)
                    token = data.get("response", "")
                    if token:
                        yield token
                    if data.get("done", False):
                        break

    async def chat(
        self,
        messages: list[dict],
        model: str = "llama3:8b",
        stream: bool = False,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str | AsyncIterator[str]:
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        if stream:
            return self._stream_chat(payload)

        response = await self.client.post("/api/chat", json=payload)
        response.raise_for_status()
        data = response.json()
        return data.get("message", {}).get("content", "")

    async def _stream_chat(self, payload: dict) -> AsyncIterator[str]:
        async with self.client.stream("POST", "/api/chat", json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.strip():
                    data = json.loads(line)
                    token = data.get("message", {}).get("content", "")
                    if token:
                        yield token
                    if data.get("done", False):
                        break

    async def list_models(self) -> list[dict]:
        response = await self.client.get("/api/tags")
        response.raise_for_status()
        return response.json().get("models", [])

    async def health_check(self) -> bool:
        try:
            response = await self.client.get("/")
            return response.status_code == 200
        except Exception:
            return False

    async def close(self) -> None:
        await self.client.aclose()
