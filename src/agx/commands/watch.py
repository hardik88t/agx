"""
Background Auto-Sync Watcher Daemon
"""

import time
from datetime import datetime

from rich.console import Console

from agx.commands.sync import execute_sync
from agx.config import CONVS_DIR

console = Console()


def _get_convs_mtime() -> float:
    if not CONVS_DIR.exists():
        return 0.0
    latest = CONVS_DIR.stat().st_mtime
    try:
        for f in CONVS_DIR.glob("*.db*"):
            try:
                mt = f.stat().st_mtime
                if mt > latest:
                    latest = mt
            except Exception:
                pass
    except Exception:
        pass
    return latest


def execute_watch(interval: int = 5):
    console.print("[bold cyan]Starting background file watcher on conversations directory...[/bold cyan]")
    console.print(f"Watching: [dim]{CONVS_DIR}[/dim] (Interval: {interval}s, Press Ctrl+C to stop)\n")

    last_mtime = _get_convs_mtime()
    try:
        while True:
            time.sleep(interval)
            current_mtime = _get_convs_mtime()
            if current_mtime > last_mtime:
                console.print(f"[{datetime.now().strftime('%H:%M:%S')}] [bold green]Detected conversation changes! Syncing...[/bold green]")
                execute_sync(quiet=True)
                console.print(f"[{datetime.now().strftime('%H:%M:%S')}] [dim]Sync complete.[/dim]")
                last_mtime = current_mtime
    except KeyboardInterrupt:
        console.print("\n[yellow]Watcher stopped.[/yellow]")
