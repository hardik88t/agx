"""
Workspace Path Rebinding Migrator
"""

from rich.console import Console

from agx.commands.sync import execute_sync
from agx.config import CLI_SUMMARIES_DB, CONVS_DIR
from agx.db import get_sqlite_conn

console = Console()


def execute_rebind(old_path: str, new_path: str):
    old_p = old_path.strip().rstrip("/")
    new_p = new_path.strip().rstrip("/")

    old_uri = old_p if old_p.startswith("file://") else f"file://{old_p}"
    new_uri = new_p if new_p.startswith("file://") else f"file://{new_p}"

    console.print(f"[bold cyan]Rebinding workspaces from '[/bold cyan]{old_uri}[bold cyan]' -> '[/bold cyan]{new_uri}[bold cyan]'...[/bold cyan]")
    rebound_count = 0

    db_files = [f for f in CONVS_DIR.glob("*.db") if f.name != "conversation_summaries.db"]
    for db_path in db_files:
        cid = db_path.stem
        try:
            conn = get_sqlite_conn(db_path, timeout=5.0)
            curr = conn.cursor()
            curr.execute("SELECT data FROM trajectory_metadata_blob WHERE id='main'")
            row = curr.fetchone()
            if row and row[0]:
                blob = row[0]
                if old_uri.encode("utf-8") in blob or old_p.encode("utf-8") in blob:
                    new_blob = blob.replace(old_uri.encode("utf-8"), new_uri.encode("utf-8")).replace(
                        old_p.encode("utf-8"), new_p.encode("utf-8")
                    )
                    curr.execute("UPDATE trajectory_metadata_blob SET data=? WHERE id='main'", (new_blob,))
                    conn.commit()
                    rebound_count += 1
                    console.print(f"  [dim]Rebound conversation:[/dim] [cyan]{cid[:8]}[/cyan]")
            conn.close()
        except Exception as e:
            console.print(f"  [red]Failed to rebind {cid[:8]}: {e}[/red]")

    cli_conn = get_sqlite_conn(CLI_SUMMARIES_DB, timeout=5.0)
    cli_conn.execute("UPDATE conversation_summaries SET workspace_uris = replace(workspace_uris, ?, ?) WHERE workspace_uris LIKE ?", (old_uri, new_uri, f"%{old_uri}%"))
    cli_conn.commit()
    cli_conn.close()

    console.print(f"\n[bold green]✔ Rebound {rebound_count} conversations. Running index sync...[/bold green]")
    execute_sync(quiet=True)
