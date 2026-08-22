"""Command-line interface for Dictionarian."""

import webbrowser
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel

from .api import DictionarianClient
from .auth import delete_token, get_token, store_token
from .constants import DEFAULT_API_URL, DEFAULT_APP_URL
from .errors import DictionarianError
from .project import PROJECT_TEMPLATE, load_project_config
from .runner import run_generation

app = typer.Typer(no_args_is_help=True, help="Generate a data dictionary from your local database.")
auth_app = typer.Typer(no_args_is_help=True, help="Manage your Dictionarian access token.")
app.add_typer(auth_app, name="auth")
console = Console()


def _fail(exc: Exception) -> None:
    console.print(f"[red]Error:[/red] {exc}")
    raise typer.Exit(code=1)


@app.command()
def init(path: Path = typer.Option(Path("dictionarian.toml"), "--path", help="Project file to create.")) -> None:
    """Create a safe starter project configuration."""
    if path.exists():
        _fail(DictionarianError(f"Refusing to overwrite existing file: {path}"))
    path.write_text(PROJECT_TEMPLATE, encoding="utf-8")
    console.print(f"Created [bold]{path}[/bold]")
    console.print("Set DICTIONARIAN_DB_PASSWORD, review the file, then run `dictionarian generate`.")


@auth_app.command("login")
def auth_login(
    api_url: str = typer.Option(DEFAULT_API_URL, help="Control-plane API URL."),
    no_browser: bool = typer.Option(False, help="Do not open the token dashboard."),
) -> None:
    """Store a token copied from the Dictionarian dashboard."""
    if not no_browser:
        webbrowser.open(f"{DEFAULT_APP_URL}/dashboard?tab=tokens")
    supplied_token = typer.prompt("Dictionarian access token", hide_input=True)
    try:
        with DictionarianClient(supplied_token, api_url=api_url) as client:
            balance = client.balance()
        store_token(supplied_token)
    except DictionarianError as exc:
        _fail(exc)
    console.print(f"Authenticated. Available credit: [bold]{balance.get('available_credits', 0):,}[/bold]")


@auth_app.command("logout")
def auth_logout() -> None:
    """Remove the access token from the operating-system keyring."""
    try:
        delete_token()
    except DictionarianError as exc:
        _fail(exc)
    console.print("Signed out.")


@app.command()
def credits(
    api_url: str = typer.Option(DEFAULT_API_URL, help="Control-plane API URL."),
) -> None:
    """Show the current prepaid credit balance."""
    try:
        with DictionarianClient(get_token(), api_url=api_url) as client:
            balance = client.balance()
    except DictionarianError as exc:
        _fail(exc)
    console.print(
        Panel(
            f"Available: [bold]{balance.get('available_credits', 0):,} credits[/bold]\n"
            f"Reserved: {balance.get('reserved_credits', 0):,} credits",
            title="Dictionarian credit balance",
        )
    )


@app.command()
def plan(config: Path = typer.Option(Path("dictionarian.toml"), "--config")) -> None:
    """Preview the local and outbound data boundary without using credits."""
    try:
        project = load_project_config(config)
        project.database.password()
    except DictionarianError as exc:
        _fail(exc)
    outbound = ["schema names", "table and column metadata", "relationships", "aggregate row counts"]
    if project.generation.include_code_context:
        outbound.extend(["selected source excerpts", "normalized source locations"])
    if project.generation.profile_sample_values:
        outbound.append("representative database values")
    console.print("Local-only: database credentials, database connection, and SQL queries")
    console.print("Sent for managed inference:")
    for category in outbound:
        console.print(f"  - {category}")
    console.print("No request was sent and no credits were consumed.")


@app.command()
def doctor(config: Path = typer.Option(Path("dictionarian.toml"), "--config")) -> None:
    """Validate local configuration, credentials, and service access."""
    try:
        project = load_project_config(config)
        project.database.password()
        with DictionarianClient(get_token(), api_url=project.api_url) as client:
            balance = client.balance()
    except DictionarianError as exc:
        _fail(exc)
    console.print("Configuration is valid.")
    console.print(f"Database: {project.database.dialect} at {project.database.host or project.database.path}")
    console.print(f"Available credit: {balance.get('available_credits', 0):,}")


@app.command()
def generate(
    config: Path = typer.Option(Path("dictionarian.toml"), "--config", help="Path to the project TOML file."),
) -> None:
    """Query the database locally and generate its data dictionary."""
    try:
        project = load_project_config(config)
        token = get_token()
        with DictionarianClient(token, api_url=project.api_url) as client:
            balance = client.balance()
        if int(balance.get("available_credits", 0)) <= 0:
            raise DictionarianError(f"No credits available. Add credit at {DEFAULT_APP_URL}/dashboard.")
        console.print(
            "Database access stays local. The categories shown by `dictionarian plan` "
            "are sent for managed inference."
        )
        if project.generation.include_code_context:
            console.print("[yellow]Source-code context is enabled for this run.[/yellow]")
        if project.generation.profile_sample_values:
            console.print("[yellow]Sample-value profiling is enabled for this run.[/yellow]")
        output = run_generation(project, token)
    except (DictionarianError, RuntimeError) as exc:
        _fail(exc)
    console.print(f"Data dictionary generated at [bold]{output}[/bold]")


def main() -> None:
    """Run the Typer application."""
    app()


if __name__ == "__main__":
    main()
