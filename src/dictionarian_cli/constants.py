"""Product defaults shared by the CLI and SDK."""

import os

DEFAULT_API_URL = os.getenv("DICTIONARIAN_API_URL", "https://api.dictionarian.ai").rstrip("/")
DEFAULT_APP_URL = os.getenv("DICTIONARIAN_APP_URL", "https://app.dictionarian.ai").rstrip("/")
DEFAULT_MODEL = os.getenv("DICTIONARIAN_MODEL", "dictionarian-default")
KEYRING_SERVICE = "dictionarian-cli"
KEYRING_USERNAME = "access-token"
TOKEN_ENV_VAR = "DICTIONARIAN_TOKEN"

