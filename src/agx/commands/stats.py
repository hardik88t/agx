"""
Analytics & Statistics Command
"""

from rich.console import Console

from agx.config import CLI_SUMMARIES_DB, CONVS_DIR, format_workspace_uri
from agx.db import get_sqlite_conn

console = Console()


def execute_stats():
    console.print("[bold cyan]Computing Antigravity workspace and session analytics...[/bold cyan]\n")
    if not CLI_SUMMARIES_DB.exists():
        console.print("[yellow]No conversation records found (CLI database not initialized). Run 'agx sync' first.[/yellow]")
        return

    conn = get_sqlite_conn(CLI_SUMMARIES_DB, readonly=True)
    try:
        rows = conn.execute("SELECT conversation_id, title, step_count, last_modified_time, workspace_uris FROM conversation_summaries").fetchall()
    except Exception:
        rows = []
    finally:
        conn.close()

    if not rows:
        console.print("[yellow]No conversation records found.[/yellow]")
        return

    total_convs = len(rows)
    total_steps = sum(r[2] for r in rows)
    avg_steps = total_steps / total_convs if total_convs else 0

    workspace_counts = {}
    dates = []
    for cid, title, steps, mtime, ws in rows:
        ws_name = format_workspace_uri(ws)
        workspace_counts[ws_name] = workspace_counts.get(ws_name, 0) + 1
        if mtime:
            dates.append(str(mtime)[:10])

    top_workspaces = sorted(workspace_counts.items(), key=lambda x: x[1], reverse=True)
    top_convs_by_steps = sorted(rows, key=lambda x: x[2], reverse=True)[:5]

    total_disk_bytes = sum(p.stat().st_size for p in CONVS_DIR.glob("*.db")) if CONVS_DIR.exists() else 0
    disk_mb = total_disk_bytes / (1024 * 1024)
    unique_active_days = len(set(dates))

    console.print("[bold magenta]" + "=" * 60 + "[/bold magenta]")
    console.print(" [bold]📊 Antigravity Workspace & Session Analytics[/bold]")
    console.print("[bold magenta]" + "=" * 60 + "[/bold magenta]")
    console.print(f"• Total Conversations   : [bold cyan]{total_convs}[/bold cyan]")
    console.print(f"• Total Agent Steps     : [bold cyan]{total_steps:,}[/bold cyan]")
    console.print(f"• Average Steps / Chat  : [bold cyan]{avg_steps:.1f}[/bold cyan]")
    console.print(f"• Unique Active Days    : [bold cyan]{unique_active_days}[/bold cyan]")
    console.print(f"• Total Disk Footprint  : [bold cyan]{disk_mb:.2f} MB[/bold cyan]")
    console.print("[bold magenta]" + "=" * 60 + "[/bold magenta]")

    console.print("\n[bold]• Conversations by Workspace:[/bold]")
    for ws, count in top_workspaces[:8]:
        pct = (count / total_convs) * 100
        bar = "█" * int(pct / 4)
        console.print(f"  {ws:<35} : [cyan]{count:3d}[/cyan] ({pct:4.1f}%) [green]{bar}[/green]")

    console.print("\n[bold]• Top 5 Largest Conversations by Step Count:[/bold]")
    for cid, title, steps, mtime, ws in top_convs_by_steps:
        console.print(f"  [{cid[:8]}] [bold cyan]{steps:4d}[/bold cyan] steps | {str(mtime)[:10]} | {title[:40]}")
    console.print("[bold magenta]" + "=" * 60 + "[/bold magenta]")
