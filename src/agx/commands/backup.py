"""
Snapshot Backup & Restore
"""

import shutil
import sys
import tarfile
from datetime import datetime
from pathlib import Path
from typing import Optional

from rich.console import Console

from agx.commands.sync import execute_sync
from agx.config import BACKUP_DIR, BRAIN_DIR, CLI_SUMMARIES_DB, CONVS_DIR, IDE_STATE_DB
from agx.utils.process import is_ide_running

console = Console()


def execute_backup(output_path: Optional[str] = None):
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = Path(output_path) if output_path else (BACKUP_DIR / f"antigravity_backup_{ts}.tar.gz")

    console.print(f"[bold cyan]Creating full state snapshot at:[/bold cyan] {dest} ...")
    with tarfile.open(dest, "w:gz") as tar:
        if CONVS_DIR.exists():
            tar.add(CONVS_DIR, arcname="conversations")
        if BRAIN_DIR.exists():
            tar.add(BRAIN_DIR, arcname="brain")
        if CLI_SUMMARIES_DB.exists():
            tar.add(CLI_SUMMARIES_DB, arcname="conversation_summaries.db")
        if IDE_STATE_DB.exists():
            tar.add(IDE_STATE_DB, arcname="state.vscdb")

    size_mb = dest.stat().st_size / (1024 * 1024)
    console.print(f"[bold green]✔ Backup created successfully! Size: {size_mb:.2f} MB[/bold green]")


def execute_restore(archive_path: str):
    archive = Path(archive_path)
    if not archive.exists():
        console.print(f"[bold red]ERROR: Archive file '{archive}' does not exist.[/bold red]")
        return

    if is_ide_running():
        console.print("[bold red]ERROR: Antigravity IDE is currently running. Please close it before restoring.[/bold red]")
        return

    console.print(f"[bold cyan]Restoring Antigravity state from '{archive}'...[/bold cyan]")
    tmp_extract = BACKUP_DIR / "tmp_restore"
    shutil.rmtree(tmp_extract, ignore_errors=True)
    tmp_extract.mkdir(parents=True, exist_ok=True)

    with tarfile.open(archive, "r:gz") as tar:
        if sys.version_info >= (3, 12):
            tar.extractall(tmp_extract, filter="data")
        else:
            tar.extractall(tmp_extract)

    rest_convs = tmp_extract / "conversations"
    if rest_convs.exists():
        shutil.copytree(rest_convs, CONVS_DIR, dirs_exist_ok=True)

    rest_brain = tmp_extract / "brain"
    if rest_brain.exists():
        shutil.copytree(rest_brain, BRAIN_DIR, dirs_exist_ok=True)

    rest_cli_db = tmp_extract / "conversation_summaries.db"
    if rest_cli_db.exists():
        shutil.copyfile(rest_cli_db, CLI_SUMMARIES_DB)

    rest_state_db = tmp_extract / "state.vscdb"
    if rest_state_db.exists():
        shutil.copyfile(rest_state_db, IDE_STATE_DB)

    shutil.rmtree(tmp_extract, ignore_errors=True)
    console.print("[bold green]✔ Files restored. Running index sync...[/bold green]")
    execute_sync(quiet=True)
