"""Bridge from the commercial CLI to the local open-source generator."""

import os
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from pathlib import Path

from .project import ProjectConfig


def build_generator_environment(project: ProjectConfig) -> dict[str, str]:
    """Build the generator environment without sending database credentials remotely."""
    database = project.database
    output = project.generation.output_dir
    safe_repo_root = output / ".local-context-disabled"
    repo_root = project.generation.repo_root if project.generation.include_code_context else safe_repo_root
    environment = {
        "DATABASE_SOURCES": database.dialect,
        "LLM_PROVIDER": "openai",
        "OPENAI_API_KEY": "not-used-hosted-provider",
        "OPENAI_BASE_URL": f"{project.api_url}/v1",
        "OPENAI_MODEL": project.generation.model,
        "LLM_CHEAP_MODEL": project.generation.model,
        "REPO_ROOT": str(repo_root),
        "ARTIFACTS_PATH": str(output / ".artifacts"),
        "DOCS_OUTPUT_PATH": str(output),
        "OUTPUT_SINK": "markdown",
        "CONFLUENCE_ENABLED": "false",
    }
    if database.dialect == "sqlite":
        environment["SQLITE_PATH"] = str(Path(database.path).expanduser().resolve())
    elif database.dialect == "postgres":
        environment.update(
            {
                "POSTGRES_HOST": database.host,
                "POSTGRES_PORT": str(database.port or 5432),
                "POSTGRES_DB": database.name,
                "POSTGRES_USER": database.user,
                "POSTGRES_PASSWORD": database.password(),
                "POSTGRES_SCHEMA": database.schema,
            }
        )
        if database.sslmode:
            environment["POSTGRES_SSLMODE"] = database.sslmode
    elif database.dialect == "redshift":
        environment.update(
            {
                "REDSHIFT_HOST": database.host,
                "REDSHIFT_PORT": str(database.port or 5439),
                "REDSHIFT_DB": database.name,
                "REDSHIFT_USER": database.user,
                "REDSHIFT_PASSWORD": database.password(),
                "REDSHIFT_SCHEMA": database.schema,
            }
        )
    elif database.dialect == "mssql":
        environment.update(
            {
                "SQLSERVER_HOST": database.host,
                "SQLSERVER_PORT": str(database.port or 1433),
                "SQLSERVER_DATABASES": database.name,
                "SQLSERVER_USER": database.user,
                "SQLSERVER_PASSWORD": database.password(),
            }
        )
    return environment


@contextmanager
def _temporary_environment(values: Mapping[str, str]) -> Iterator[None]:
    original = {key: os.environ.get(key) for key in values}
    os.environ.update(values)
    try:
        yield
    finally:
        for key, value in original.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def run_generation(project: ProjectConfig, token: str) -> Path:
    """Run the data dictionary workflow locally and return its output path."""
    environment = build_generator_environment(project)
    project.generation.output_dir.mkdir(parents=True, exist_ok=True)
    (project.generation.output_dir / ".local-context-disabled").mkdir(mode=0o700, parents=True, exist_ok=True)
    previous_umask = os.umask(0o077)
    try:
        with _temporary_environment(environment):
            # Imports are intentionally delayed until the isolated environment
            # is present because dictionarian_ai constructs settings at import.
            from dictionarian_ai import workflow
            from dictionarian_ai.settings import Config

            from .provider import HostedLLMAgent

            original_provider_factory = Config.create_llm_agent

            def create_hosted_agent(self: Config, use_cheap_model: bool = False) -> HostedLLMAgent:
                return HostedLLMAgent(
                    token=token,
                    api_url=project.api_url,
                    model_name=project.generation.model,
                )

            Config.create_llm_agent = create_hosted_agent

            if not project.generation.include_code_context:

                def skip_code_refs(state: workflow.GraphState) -> workflow.GraphState:
                    completed = list(state.get("completed_agents", []))
                    completed.append("Code Reference Miner (privacy-safe skip)")
                    state["completed_agents"] = completed
                    return state

                workflow.node_code_refs = skip_code_refs

            if not project.generation.profile_sample_values:

                def skip_profile(state: workflow.GraphState) -> workflow.GraphState:
                    completed = list(state.get("completed_agents", []))
                    completed.append("Data Profiler (privacy-safe skip)")
                    state["completed_agents"] = completed
                    return state

                workflow.node_profile = skip_profile

            try:
                final_state = workflow.run_workflow(table_examples={})
                errors = final_state.get("errors", [])
                if errors:
                    raise RuntimeError("Generation failed: " + "; ".join(str(error) for error in errors))
            finally:
                Config.create_llm_agent = original_provider_factory
    finally:
        os.umask(previous_umask)
    return project.generation.output_dir
