"""LLMClient tests: request construction, error handling, configuration."""

import httpx
import pytest

from skill_eval.judge.client import LLMClient, LLMError


def _handler(request: httpx.Request) -> httpx.Response:
    assert request.url.path == "/v1/chat/completions"
    assert request.headers["authorization"] == "Bearer test-key"
    body = request.read().decode()
    assert '"model":"mock-model"' in body
    assert '"messages"' in body
    return httpx.Response(
        200,
        json={"choices": [{"message": {"content": '{"score": 0.9}'}}]},
    )


def _client(api_key: str = "test-key") -> LLMClient:
    return LLMClient(
        base_url="http://mock/v1",
        api_key=api_key,
        model="mock-model",
        transport=httpx.MockTransport(_handler),
    )


class TestLLMClient:
    def test_complete_returns_content(self) -> None:
        out = _client().complete([{"role": "user", "content": "hi"}])
        assert out == '{"score": 0.9}'

    def test_not_configured_raises(self) -> None:
        with pytest.raises(LLMError, match="not configured"):
            _client(api_key=None).complete([{"role": "user", "content": "hi"}])

    def test_provider_error_raises(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(429, text="rate limited")

        client = LLMClient(
            base_url="http://mock/v1",
            api_key="k",
            model="m",
            transport=httpx.MockTransport(handler),
        )
        with pytest.raises(LLMError, match="429"):
            client.complete([{"role": "user", "content": "hi"}])

    def test_malformed_response_raises(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"choices": []})

        client = LLMClient(
            base_url="http://mock/v1",
            api_key="k",
            model="m",
            transport=httpx.MockTransport(handler),
        )
        with pytest.raises(LLMError):
            client.complete([{"role": "user", "content": "hi"}])
