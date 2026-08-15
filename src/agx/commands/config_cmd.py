from importlib.resources import files

from rich.console import Console

from agx.config import AGX_CONFIG_DIR, CONFIG_FILE

console = Console()


def get_default_config_template() -> str:
    try:
        return files("agx").joinpath("config.example.toml").read_text(encoding="utf-8")
    except Exception:
        return """# AGX Configuration
[versions]
target_cli_version = "1.1.13"
target_ide_version = "2.5.5"
"""


def execute_config_init(force: bool = False):
    if CONFIG_FILE.exists() and not force:
        console.print(f"[yellow]Config file already exists at:[/yellow] {CONFIG_FILE}")
        console.print("Use [bold cyan]agx config init --force[/bold cyan] to overwrite.")
        return

    AGX_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    content = get_default_config_template()
    CONFIG_FILE.write_text(content, encoding="utf-8")
    console.print(f"[bold green]✔ Configuration file initialized at:[/bold green] {CONFIG_FILE}")



def execute_config_show():
    console.print(f"[bold cyan]Config Path:[/bold cyan] {CONFIG_FILE}")
    if not CONFIG_FILE.exists():
        console.print("[dim]Config file does not exist (using default dynamic paths).[/dim]")
        console.print("Run [bold cyan]agx config init[/bold cyan] to create a template.")
        return

    console.print("\n[bold]Current configuration:[/bold]")
    console.print(CONFIG_FILE.read_text(encoding="utf-8"))
