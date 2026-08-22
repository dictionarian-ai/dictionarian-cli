"""Tests for the hosted generator provider contract."""

from dictionarian_cli.provider import HostedLLMAgent


class _FakeClient:
    def inference(self, **kwargs):
        assert kwargs["operation"] in {"generate", "table_summary"}
        return {
            "content": '{"summary": "A useful summary"}' if kwargs["operation"] == "generate" else "A useful summary",
            "model": "managed-model",
            "usage": {"prompt_tokens": 10, "completion_tokens": 3, "total_tokens": 13},
            "credits_charged": 2,
            "balance_after": 98,
            "request_id": "req_123",
        }


def test_hosted_provider_returns_generator_response() -> None:
    agent = HostedLLMAgent("dict_test_token", "https://api.example.test")
    agent._client = _FakeClient()

    response = agent.generate("Summarize this", operation="table_summary")

    assert response.content == "A useful summary"
    assert response.metadata["credits_charged"] == 2


def test_hosted_json_uses_a_server_allowed_operation() -> None:
    agent = HostedLLMAgent("dict_test_token", "https://api.example.test")
    agent._client = _FakeClient()

    assert agent.generate_json("Return a summary") == {"summary": "A useful summary"}
