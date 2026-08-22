"""Managed inference provider injected into the local generator at runtime."""

import json
from typing import Any

from dictionarian_ai.llm.base_agent import BaseLLMAgent, LLMResponse

from .api import DictionarianClient


class HostedLLMAgent(BaseLLMAgent):
    """Route generator prompts through Dictionarian without a user model key."""

    def __init__(self, token: str, api_url: str, model_name: str = "dictionarian-default", **kwargs: Any) -> None:
        super().__init__(model_name=model_name, api_key=None, track_tokens=False, **kwargs)
        self._product_token = token
        self._api_url = api_url

    def _initialize_client(self) -> DictionarianClient:
        return DictionarianClient(self._product_token, api_url=self._api_url, timeout=120.0)

    def _make_request(self, messages: list[dict[str, str]], **kwargs: Any) -> LLMResponse:
        payload = self.client.inference(
            messages=messages,
            operation=str(kwargs.pop("operation", "generate")),
            temperature=float(kwargs.get("temperature", 0.3)),
            max_tokens=kwargs.get("max_tokens"),
        )
        usage = payload.get("usage")
        return LLMResponse(
            content=str(payload["content"]),
            model=str(payload.get("model", self.model_name)),
            usage=dict(usage) if isinstance(usage, dict) else None,
            metadata={
                "request_id": payload.get("request_id"),
                "credits_charged": payload.get("credits_charged"),
                "balance_after": payload.get("balance_after"),
            },
        )

    def generate(
        self,
        prompt: str,
        system_message: str | None = None,
        temperature: float = 0.3,
        max_tokens: int | None = None,
        operation: str = "generate",
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate while preserving the operation name for server policy and metering."""
        messages: list[dict[str, str]] = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})
        request_kwargs = {"temperature": temperature, "operation": operation, **kwargs}
        if max_tokens is not None:
            request_kwargs["max_tokens"] = max_tokens
        return self._make_request(messages, **request_kwargs)

    def generate_json(
        self,
        prompt: str,
        system_message: str | None = None,
        temperature: float = 0.2,
        max_tokens: int | None = None,
        operation: str = "generate",
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Generate and parse a JSON object through the managed endpoint."""
        response = self.generate(
            prompt=f"{prompt}\n\nReturn only valid JSON.",
            system_message=system_message,
            temperature=temperature,
            max_tokens=max_tokens,
            operation=operation,
            **kwargs,
        )
        content = response.content.strip()
        if content.startswith("```"):
            lines = content.splitlines()
            content = "\n".join(lines[1:-1] if lines and lines[-1].strip() == "```" else lines[1:])
        parsed = json.loads(content)
        if not isinstance(parsed, dict):
            raise ValueError("Managed inference returned JSON that was not an object.")
        return parsed

    def generate_with_json_template(
        self,
        template_name: str,
        system_template: str | None = None,
        temperature: float = 0.2,
        max_tokens: int | None = None,
        operation: str | None = None,
        **context: Any,
    ) -> dict[str, Any]:
        """Render generator templates locally and request a JSON result."""
        from dictionarian_ai.services.prompt_service import prompt_service

        prompt = prompt_service.render(template_name, **context)
        system_message = prompt_service.render(system_template, **context) if system_template else None
        return self.generate_json(
            prompt=prompt,
            system_message=system_message,
            temperature=temperature,
            max_tokens=max_tokens,
            operation=operation or template_name,
        )
