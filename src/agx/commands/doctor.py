"""
Diagnostic Health Check
"""

from rich.console import Console

from agx.config import (
    BRAIN_DIR,
    CLI_DIR,
    CLI_SUMMARIES_DB,
    CONVS_DIR,
    IDE_DIR,
    IDE_STATE_DB,
    TARGET_CLI_VERSION,
    TARGET_IDE_VERSION,
    get_cli_version,
    get_ide_version,
)
from agx.db import check_db_integrity
from agx.utils.process import is_ide_running

console = Console()


def execute_doctor():
    console.print("[bold magenta]" + "=" * 70 + "[/bold magenta]")
    console.print(" [bold]🩺 Antigravity Diagnostic Health Check[/bold]")
    console.print("[bold magenta]" + "=" * 70 + "[/bold magenta]")

    cli_v = get_cli_version()
    ide_v = get_ide_version()
    console.print(f"• CLI Version : [bold]{cli_v}[/bold] (Target: {TARGET_CLI_VERSION}) -> {'[green]✅ OK[/green]' if cli_v == TARGET_CLI_VERSION else '[yellow]⚠️ Mismatch[/yellow]'}")
    console.print(f"• IDE Version : [bold]{ide_v}[/bold] (Target: {TARGET_IDE_VERSION}) -> {'[green]✅ OK[/green]' if ide_v == TARGET_IDE_VERSION else '[yellow]⚠️ Mismatch[/yellow]'}")

    console.print("\n[bold]• Symlink Integrity (CLI -> IDE):[/bold]")
    for name in ["brain", "conversations", "mcp", "knowledge"]:
        p = CLI_DIR / name
        target = IDE_DIR / name
        if p.is_symlink():
            actual = p.resolve()
            status = "[green]✅ Valid[/green]" if actual == target.resolve() else f"[red]❌ Points to {actual}[/red]"
            console.print(f"  - {name:<14} : {status}")
        else:
            console.print(f"  - {name:<14} : [red]❌ Not a symlink![/red]")

    console.print("\n[bold]• Database Integrity:[/bold]")
    for name, path in [("CLI Summaries", CLI_SUMMARIES_DB), ("IDE Global State", IDE_STATE_DB)]:
        res = check_db_integrity(path)
        status = "[green]✅ OK[/green]" if res == "ok" else f"[red]❌ {res}[/red]"
        console.print(f"  - {name:<16} : {status}")

    conv_count = len(list(CONVS_DIR.glob("*.db")))
    brain_count = len([d for d in BRAIN_DIR.iterdir() if d.is_dir()]) if BRAIN_DIR.exists() else 0
    console.print("\n[bold]• Storage Statistics:[/bold]")
    console.print(f"  - Total Conversations on Disk : [cyan]{conv_count}[/cyan]")
    console.print(f"  - Total Brain Folders         : [cyan]{brain_count}[/cyan]")

    ide_running = is_ide_running()
    console.print("\n[bold]• Process Status:[/bold]")
    console.print(f"  - Antigravity IDE             : {'[green]🟢 Running[/green]' if ide_running else '[dim]⚪ Stopped[/dim]'}")
    console.print("[bold magenta]" + "=" * 70 + "[/bold magenta]")
