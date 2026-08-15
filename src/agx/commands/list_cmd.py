"""
List Conversations Command
"""

from typing import Optional

from rich.console import Console
from rich.table import Table

from agx.config import CLI_SUMMARIES_DB, format_workspace_uri
from agx.db import get_sqlite_conn

console = Console()


def execute_list(limit: int = 25, workspace: Optional[str] = None):
    if not CLI_SUMMARIES_DB.exists():
        console.print("[yellow]No conversations found (CLI database not initialized). Run 'agx sync' first.[/yellow]")
        return

    conn = get_sqlite_conn(CLI_SUMMARIES_DB, readonly=True)
    curr = conn.cursor()

    try:
        query = "SELECT conversation_id, title, step_count, last_modified_time, workspace_uris FROM conversation_summaries"
        params = []
        if workspace:
            query += " WHERE workspace_uris LIKE ?"
            params.append(f"%{workspace}%")
        query += " ORDER BY last_modified_time DESC"
        if limit > 0:
            query += f" LIMIT {limit}"

        rows = curr.execute(query, params).fetchall()
    except Exception:
        rows = []
    finally:
        conn.close()

    if not rows:
        console.print("[yellow]No conversations found.[/yellow]")
        return

    table = Table(title="Antigravity Conversations", show_header=True, header_style="bold magenta")
    table.add_column("UUID", style="cyan", width=36)
    table.add_column("Steps", justify="right", width=6)
    table.add_column("Last Modified", style="dim", width=19)
    table.add_column("Workspace", style="green", width=25)
    table.add_column("Title", style="white")

    for cid, title, steps, mtime, ws in rows:
        ws_short = format_workspace_uri(ws)
        table.add_row(cid, str(steps), str(mtime)[:19], ws_short, title)

    console.print(table)
    console.print(f"[dim]Total shown: {len(rows)}[/dim]")
