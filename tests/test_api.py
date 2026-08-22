"""Tests for API authentication and error mapping."""

import httpx
import pytest

from dictionarian_cli.api import DictionarianClient
from dictionarian_cli.errors import InsufficientCreditsError


def test_balance_sends_customer_bearer_token() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == "Bearer dict_test_example"
        return httpx.Response(200, json={"available_credits": 100, "reserved_credits": 0})

    with DictionarianClient(
        "dict_test_example",
        api_url="https://api.example.test",
        transport=httpx.MockTransport(handler),
    ) as client:
        assert client.balance()["available_credits"] == 100


def test_payment_required_maps_to_credit_error() -> None:
    transport = httpx.MockTransport(lambda request: httpx.Response(402, json={"detail": "Add credits"}))
    with DictionarianClient("dict_test_example", transport=transport) as client:
        with pytest.raises(InsufficientCreditsError, match="Add credits"):
            client.balance()
