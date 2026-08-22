"""Tests for the generator bridge environment."""

from pathlib import Path

from dictionarian_cli.project import DatabaseConfig, GenerationConfig, ProjectConfig
from dictionarian_cli.runner import build_generator_environment


def test_remote_model_proxy_is_injected_without_provider_key(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("WAREHOUSE_PASSWORD", "local-only-secret")
    project = ProjectConfig(
        database=DatabaseConfig(
            dialect="postgres",
            host="localhost",
            name="analytics",
            user="readonly",
            password_env="WAREHOUSE_PASSWORD",
        ),
        generation=GenerationConfig(repo_root=tmp_path, output_dir=tmp_path / "out"),
        api_url="https://api.example.test",
    )

    environment = build_generator_environment(project)

    assert environment["OPENAI_BASE_URL"] == "https://api.example.test/v1"
    assert environment["OPENAI_API_KEY"] == "not-used-hosted-provider"
    assert environment["POSTGRES_PASSWORD"] == "local-only-secret"
    assert "ANTHROPIC_API_KEY" not in environment
    assert environment["CONFLUENCE_ENABLED"] == "false"
    assert environment["REPO_ROOT"].endswith(".local-context-disabled")
