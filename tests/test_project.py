"""Tests for safe local project configuration."""

from pathlib import Path

import pytest

from dictionarian_cli.errors import ConfigurationError
from dictionarian_cli.project import load_project_config


def test_load_postgres_config_resolves_paths_and_password(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_file = tmp_path / "dictionarian.toml"
    config_file.write_text(
        """
[database]
dialect = "postgres"
host = "db.internal"
port = 5432
name = "warehouse"
user = "readonly"
password_env = "TEST_DB_PASSWORD"

[generation]
repo_root = "src"
output_dir = "dictionary"
profile_sample_values = false
""",
        encoding="utf-8",
    )
    monkeypatch.setenv("TEST_DB_PASSWORD", "not-sent-remotely")

    project = load_project_config(config_file)

    assert project.database.dialect == "postgres"
    assert project.database.password() == "not-sent-remotely"
    assert project.generation.repo_root == (tmp_path / "src").resolve()
    assert project.generation.output_dir == (tmp_path / "dictionary").resolve()
    assert project.generation.include_code_context is False
    assert project.generation.profile_sample_values is False


def test_missing_password_environment_variable_is_rejected(tmp_path: Path) -> None:
    config_file = tmp_path / "dictionarian.toml"
    config_file.write_text(
        """
[database]
dialect = "mssql"
host = "db.internal"
name = "warehouse"
user = "readonly"
password_env = "MISSING_TEST_PASSWORD"
""",
        encoding="utf-8",
    )
    project = load_project_config(config_file)

    with pytest.raises(ConfigurationError, match="MISSING_TEST_PASSWORD"):
        project.database.password()


def test_sqlite_requires_a_path(tmp_path: Path) -> None:
    config_file = tmp_path / "dictionarian.toml"
    config_file.write_text('[database]\ndialect = "sqlite"\n', encoding="utf-8")

    with pytest.raises(ConfigurationError, match="database.path"):
        load_project_config(config_file)
