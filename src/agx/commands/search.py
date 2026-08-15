"""
Search Command
"""

from datetime import datetime

from rich.console import Console
from rich.table import Table

from agx.config import BRAIN_DIR, CLI_SUMMARIES_DB, CONVS_DIR
from agx.db import get_sqlite_conn
from agx.utils.transcript import get_title_from_transcript, get_workspace_from_disk

console = Console()


def execute_search(query: str):
    query_str = query.lower()
    console.print(f"[bold cyan]Searching for '[/bold cyan]{query}[bold cyan]' across conversations and transcripts...[/bold cyan]\n")
    matches = []

    conn = get_sqlite_conn(CLI_SUMMARIES_DB, readonly=True)
    rows = conn.execute("SELECT conversation_id, title, workspace_uris, last_modified_time FROM conversation_summaries").fetchall()
    conn.close()

    for cid, title, ws, mtime in rows:
        if query_str in title.lower() or query_str in cid.lower():
            matches.append((cid, title, ws, mtime, "Title/UUID match"))

    for db_path in CONVS_DIR.glob("*.db"):
        cid = db_path.stem
        if any(m[0] == cid for m in matches):
            continue
        log_path = BRAIN_DIR / cid / ".system_generated" / "logs" / "transcript.jsonl"
        if log_path.exists():
            try:
                with open(log_path, "r", errors="ignore", encoding="utf-8") as f:
                    content = f.read(65536)
                    if query_str in content.lower():
                        title = get_title_from_transcript(cid) or f"Session {cid[:6]}"
                        ws = get_workspace_from_disk(cid, db_path)
                        mtime = datetime.fromtimestamp(db_path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                        matches.append((cid, title, ws, mtime, "Transcript match"))
            except Exception:
                pass

    if not matches:
        console.print("[yellow]No matching conversations found.[/yellow]")
        return

    table = Table(title=f"Search Results for '{query}'", show_header=True, header_style="bold magenta")
    table.add_column("UUID", style="cyan", width=36)
    table.add_column("Last Modified", style="dim", width=19)
    table.add_column("Match Type", style="green", width=18)
    table.add_column("Title", style="white")

    for cid, title, ws, mtime, mtype in matches:
        table.add_row(cid, str(mtime)[:19], mtype, title)

    console.print(table)
    console.print(f"[dim]Total matches: {len(matches)}[/dim]")
