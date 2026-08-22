"""Project-level configuration that never stores database passwords."""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 only
    import tomli as tomllib

from .constants import DEFAULT_API_URL, DEFAULT_MODEL
from .errors import ConfigurationError

SUPPORTED_DIALECTS = {"postgres", "mssql", "redshift", "sqlite"}


@dataclass(frozen=True)
class DatabaseConfig:
    """Connection metadata for the database queried by the local process."""

    dialect: str
    host: str = ""
    port: int | None = None
    name: str = ""
    user: str = ""
    password_env: str = ""
    schema: str = "public"
    sslmode: str = ""
    path: str = ""

    def password(self) -> str:
        """Resolve the password from the configured environment variable."""
        if self.dialect == "sqlite":
            return ""
        if not self.password_env:
            raise ConfigurationError("database.password_env is required and must name an environment variable.")
        value = os.getenv(self.password_env)
        if not value:
            raise ConfigurationError(f"Environment variable {self.password_env} is not set.")
        return value


@dataclass(frozen=True)
class GenerationConfig:
    """Local generation and privacy settings."""

    repo_root: Path
    output_dir: Path
    model: str = DEFAULT_MODEL
    include_code_context: bool = False
    profile_sample_values: bool = False


@dataclass(frozen=True)
class ProjectConfig:
    """Complete local project configuration."""

    database: DatabaseConfig
    generation: GenerationConfig
    api_url: str = DEFAULT_API_URL


def _resolve_path(base: Path, raw: str, default: str) -> Path:
    value = Path(raw or default).expanduser()
    return value.resolve() if value.is_absolute() else (base / value).resolve()


def load_project_config(path: Path | str = "dictionarian.toml") -> ProjectConfig:
    """Load and validate a Dictionarian TOML project file."""
    config_path = Path(path).expanduser().resolve()
    if not config_path.is_file():
        raise ConfigurationError(f"Project file not found: {config_path}. Run `dictionarian init` first.")
    with config_path.open("rb") as handle:
        raw = tomllib.load(handle)

    database_raw: dict[str, Any] = raw.get("database", {})
    generation_raw: dict[str, Any] = raw.get("generation", {})
    service_raw: dict[str, Any] = raw.get("service", {})
    dialect = str(database_raw.get("dialect", "")).lower()
    if dialect not in SUPPORTED_DIALECTS:
        supported = ", ".join(sorted(SUPPORTED_DIALECTS))
        raise ConfigurationError(f"database.dialect must be one of: {supported}.")

    database = DatabaseConfig(
        dialect=dialect,
        host=str(database_raw.get("host", "")),
        port=int(database_raw["port"]) if database_raw.get("port") else None,
        name=str(database_raw.get("name", "")),
        user=str(database_raw.get("user", "")),
        password_env=str(database_raw.get("password_env", "")),
        schema=str(database_raw.get("schema", "public")),
        sslmode=str(database_raw.get("sslmode", "")),
        path=str(database_raw.get("path", "")),
    )
    if dialect == "sqlite" and not database.path:
        raise ConfigurationError("database.path is required for SQLite.")
    if dialect != "sqlite" and not all((database.host, database.name, database.user)):
        raise ConfigurationError("database.host, database.name, and database.user are required.")

    base = config_path.parent
    generation = GenerationConfig(
        repo_root=_resolve_path(base, str(generation_raw.get("repo_root", ".")), "."),
        output_dir=_resolve_path(base, str(generation_raw.get("output_dir", "data-dictionary")), "data-dictionary"),
        model=str(generation_raw.get("model", DEFAULT_MODEL)),
        include_code_context=bool(generation_raw.get("include_code_context", False)),
        profile_sample_values=bool(generation_raw.get("profile_sample_values", False)),
    )
    return ProjectConfig(
        database=database,
        generation=generation,
        api_url=str(service_raw.get("api_url", DEFAULT_API_URL)).rstrip("/"),
    )


PROJECT_TEMPLATE = """# Dictionarian queries this database only from your machine.
# Create a read-only database user. Never put its password in this file.
[database]
dialect = "postgres"
host = "localhost"
port = 5432
name = "analytics"
user = "dictionarian_readonly"
password_env = "DICTIONARIAN_DB_PASSWORD"
schema = "public"
sslmode = "require"

[generation]
repo_root = "."
output_dir = "data-dictionary"
model = "dictionarian-default"

# Both are off by default. When enabled, source excerpts or representative
# database values can be included in prompts sent to Dictionarian's service.
include_code_context = false
profile_sample_values = false

[service]
api_url = "https://api.dictionarian.ai"
"""
