"""
Orphaned Records & Temp Files Cleanup
"""

from rich.console import Console

from agx.config import CLI_SUMMARIES_DB, CONVS_DIR
from agx.db import get_sqlite_conn

console = Console()


def execute_prune():
    console.print("[bold cyan]Scanning for orphaned records and dangling temporary files...[/bold cyan]")
    pruned_files = 0
    pruned_db_rows = 0

    for tmp_file in CONVS_DIR.glob("*.tmp*"):
        try:
            tmp_file.unlink()
            pruned_files += 1
            console.print(f"  [dim]Removed temp file:[/dim] {tmp_file.name}")
        except Exception as e:
            console.print(f"  [red]Failed to remove {tmp_file}: {e}[/red]")

    cli_conn = get_sqlite_conn(CLI_SUMMARIES_DB, timeout=5.0)
    curr = cli_conn.cursor()
    rows = curr.execute("SELECT conversation_id FROM conversation_summaries").fetchall()
    for (cid,) in rows:
        db_file = CONVS_DIR / f"{cid}.db"
        if not db_file.exists():
            curr.execute("DELETE FROM conversation_summaries WHERE conversation_id=?", (cid,))
            pruned_db_rows += 1
            console.print(f"  [dim]Pruned orphaned index row:[/dim] [cyan]{cid[:8]}[/cyan]")
    cli_conn.commit()
    cli_conn.close()

    console.print(f"\n[bold green]✔ Prune complete: Removed {pruned_files} temp files, {pruned_db_rows} orphaned records.[/bold green]")
    from agx.commands.sync import execute_sync
    execute_sync(quiet=True)
