"""Secure storage and retrieval for Dictionarian access tokens."""

import os

import keyring
from keyring.errors import KeyringError

from .constants import KEYRING_SERVICE, KEYRING_USERNAME, TOKEN_ENV_VAR
from .errors import AuthenticationError


def get_token() -> str:
    """Return the token from the environment or the operating-system keyring."""
    environment_token = os.getenv(TOKEN_ENV_VAR, "").strip()
    if environment_token:
        return environment_token
    try:
        stored_token = keyring.get_password(KEYRING_SERVICE, KEYRING_USERNAME)
    except KeyringError as exc:
        raise AuthenticationError(
            f"The system keyring is unavailable. Set {TOKEN_ENV_VAR} for this process instead."
        ) from exc
    if not stored_token:
        raise AuthenticationError("Not authenticated. Run `dictionarian auth login` first.")
    return stored_token


def store_token(token: str) -> None:
    """Validate the token shape and store it in the operating-system keyring."""
    normalized = token.strip()
    if not normalized.startswith(("dict_live_", "dict_test_")) or len(normalized) < 32:
        raise AuthenticationError("That does not look like a Dictionarian access token.")
    try:
        keyring.set_password(KEYRING_SERVICE, KEYRING_USERNAME, normalized)
    except KeyringError as exc:
        raise AuthenticationError(
            f"The system keyring is unavailable. Set {TOKEN_ENV_VAR} for this process instead."
        ) from exc


def delete_token() -> None:
    """Remove the stored token if one exists."""
    try:
        existing = keyring.get_password(KEYRING_SERVICE, KEYRING_USERNAME)
        if existing:
            keyring.delete_password(KEYRING_SERVICE, KEYRING_USERNAME)
    except KeyringError as exc:
        raise AuthenticationError("The system keyring is unavailable.") from exc

