"""HTTP client for Dictionarian's metered control plane."""

from collections.abc import Mapping
from typing import Any
from uuid import uuid4

import httpx

from .constants import DEFAULT_API_URL
from .errors import AuthenticationError, DictionarianError, InsufficientCreditsError


class DictionarianClient:
    """Small synchronous SDK for account, credit, and generation APIs."""

    def __init__(
        self,
        token: str,
        api_url: str = DEFAULT_API_URL,
        timeout: float = 30.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        """Create an authenticated API client."""
        self.token = token
        self.api_url = api_url.rstrip("/")
        self._client = httpx.Client(
            base_url=self.api_url,
            headers={"Authorization": f"Bearer {token}", "User-Agent": "dictionarian-cli/0.1.0"},
            timeout=timeout,
            transport=transport,
        )

    def __enter__(self) -> "DictionarianClient":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
        """Close the underlying HTTP connection pool."""
        self._client.close()

    def health(self) -> Mapping[str, Any]:
        """Return public service health information."""
        return self._request("GET", "/health")

    def balance(self) -> Mapping[str, Any]:
        """Return the authenticated account's available credit balance."""
        return self._request("GET", "/v1/credits/balance")

    def inference(
        self,
        messages: list[dict[str, str]],
        operation: str,
        temperature: float,
        max_tokens: int | None,
        idempotency_key: str | None = None,
    ) -> Mapping[str, Any]:
        """Invoke the managed model service with server-authoritative metering."""
        return self._request(
            "POST",
            "/v1/inference",
            headers={"Idempotency-Key": idempotency_key or str(uuid4())},
            json={
                "messages": messages,
                "operation": operation,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
        )

    def _request(self, method: str, path: str, **kwargs: Any) -> Mapping[str, Any]:
        try:
            response = self._client.request(method, path, **kwargs)
        except httpx.HTTPError as exc:
            raise DictionarianError(f"Could not reach Dictionarian at {self.api_url}: {exc}") from exc

        payload: Any
        try:
            payload = response.json()
        except ValueError:
            payload = {"detail": response.text or f"HTTP {response.status_code}"}

        detail = payload.get("detail", "Request failed") if isinstance(payload, dict) else "Request failed"
        if response.status_code == 401:
            raise AuthenticationError(str(detail))
        if response.status_code == 402:
            raise InsufficientCreditsError(str(detail))
        if response.is_error:
            raise DictionarianError(f"Dictionarian API error ({response.status_code}): {detail}")
        if not isinstance(payload, Mapping):
            raise DictionarianError("Dictionarian API returned an invalid response.")
        return payload
