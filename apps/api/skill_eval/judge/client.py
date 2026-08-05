"""OpenAI-compatible chat completions client (base_url / api_key / model configurable)."""

import os
from typing import Any

import httpx


class LLMError(RuntimeError):
    pass


class LLMClient:
    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
        timeout: float = 60.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._base_url = (base_url or os.environ.get("SKILLEVAL_LLM_BASE_URL") or "https://api.openai.com/v1").rstrip("/")
        self._api_key = api_key or os.environ.get("SKILLEVAL_LLM_API_KEY")
        self._model = model or os.environ.get("SKILLEVAL_LLM_MODEL") or "gpt-4o-mini"
        self._client = httpx.Client(base_url=self._base_url, timeout=timeout, transport=transport)

    def configured(self) -> bool:
        return bool(self._api_key)

    def complete(self, messages: list[dict[str, Any]]) -> str:
        if not self._api_key:
            raise LLMError("LLM provider not configured (SKILLEVAL_LLM_API_KEY)")
        resp = self._client.post(
            "/chat/completions",
            headers={"Authorization": f"Bearer {self._api_key}"},
            json={
                "model": self._model,
                "messages": messages,
                "temperature": 0,
            },
        )
        if resp.status_code != 200:
            raise LLMError(f"LLM provider error {resp.status_code}: {resp.text[:200]}")
        data = resp.json()
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMError(f"unexpected provider response: {data!r:.200}") from exc
