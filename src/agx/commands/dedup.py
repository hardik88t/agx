"""
Duplicate Session Detector & Cleanup
"""

import hashlib
import shutil

from rich.console import Console
from rich.table import Table

from agx.commands.prune import execute_prune
from agx.config import BRAIN_DIR, CONVS_DIR
from agx.utils.transcript import get_title_from_transcript, get_workspace_from_disk

console = Console()


def execute_dedup(apply: bool = False):
    console.print("[bold cyan]Scanning conversations for duplicate threads...[/bold cyan]")
    seen_hashes = {}
    duplicates = []

    db_files = [f for f in CONVS_DIR.glob("*.db") if f.name != "conversation_summaries.db"]
    for db_path in db_files:
        cid = db_path.stem
        log_path = BRAIN_DIR / cid / ".system_generated" / "logs" / "transcript.jsonl"

        content_sig = ""
        if log_path.exists():
            try:
                with open(log_path, "rb") as f:
                    content_sig = hashlib.sha256(f.read(8192)).hexdigest()
            except Exception:
                pass

        if not content_sig:
            continue

        ws = get_workspace_from_disk(cid, db_path)
        sig = f"{ws}:{content_sig}"

        if sig in seen_hashes:
            primary_cid = seen_hashes[sig]
            duplicates.append((cid, primary_cid, get_title_from_transcript(cid) or cid[:8]))
        else:
            seen_hashes[sig] = cid

    if not duplicates:
        console.print("[green]✔ No duplicate conversation sessions detected.[/green]")
        return

    table = Table(title=f"Found {len(duplicates)} Duplicate Sessions", show_header=True, header_style="bold magenta")
    table.add_column("Duplicate UUID", style="red", width=36)
    table.add_column("Primary UUID", style="green", width=36)
    table.add_column("Title", style="white")

    for dup_cid, prim_cid, title in duplicates:
        table.add_row(dup_cid, prim_cid, title)

    console.print(table)

    if apply:
        console.print(f"\n[bold red]Removing {len(duplicates)} duplicate sessions from disk...[/bold red]")
        for dup_cid, _, _ in duplicates:
            db_file = CONVS_DIR / f"{dup_cid}.db"
            brain_folder = BRAIN_DIR / dup_cid
            try:
                if db_file.exists():
                    db_file.unlink()
                if brain_folder.exists():
                    shutil.rmtree(brain_folder, ignore_errors=True)
                console.print(f"  [dim]Removed duplicate:[/dim] [cyan]{dup_cid[:8]}[/cyan]")
            except Exception as e:
                console.print(f"  [red]Failed to remove {dup_cid[:8]}: {e}[/red]")
        execute_prune()
    else:
        console.print("\n[dim]Dry-run mode. To delete duplicate sessions, run:[/dim] [bold cyan]agx dedup --apply[/bold cyan]")
