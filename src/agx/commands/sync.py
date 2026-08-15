"""
Unified Sync Command
"""

import base64
import sqlite3
from datetime import datetime, timezone

from rich.console import Console

from agx.config import (
    CLI_SUMMARIES_DB,
    CONVS_DIR,
    IDE_STATE_DB,
    TARGET_CLI_VERSION,
    TARGET_IDE_VERSION,
    get_cli_version,
    get_ide_version,
)
from agx.db import backup_sqlite_db, get_sqlite_conn
from agx.proto import build_ide_info_proto, encode_string, encode_varint, parse_proto
from agx.utils.process import is_ide_running, start_ide, stop_ide
from agx.utils.transcript import get_title_from_transcript, get_workspace_from_disk

console = Console()


def execute_sync(quiet: bool = False, force: bool = False) -> int:
    if not quiet:
        console.print("[bold cyan]Checking versions...[/bold cyan]")
    cli_ver = get_cli_version()
    ide_ver = get_ide_version()

    if not quiet:
        console.print(f"• Detected CLI: [bold]{cli_ver}[/bold] (Target: {TARGET_CLI_VERSION})")
        console.print(f"• Detected IDE: [bold]{ide_ver}[/bold] (Target: {TARGET_IDE_VERSION})")

    if (cli_ver != TARGET_CLI_VERSION or ide_ver != TARGET_IDE_VERSION) and not force:
        console.print(f"[bold red]ERROR: Version mismatch! CLI must be {TARGET_CLI_VERSION} and IDE must be {TARGET_IDE_VERSION}.[/bold red]")
        console.print("Use --force to bypass this check if you have verified compatibility.")
        return 1

    ide_running_at_start = is_ide_running()

    # 1. Read existing summaries from IDE State DB
    if not quiet:
        console.print("[dim]Reading IDE State DB...[/dim]")
    ide_conn = get_sqlite_conn(IDE_STATE_DB)
    ide_conn.execute("CREATE TABLE IF NOT EXISTS ItemTable (key TEXT PRIMARY KEY, value BLOB)")
    row = ide_conn.execute("SELECT value FROM ItemTable WHERE key='antigravityUnifiedStateSync.trajectorySummaries'").fetchone()

    existing_summaries = {}
    if row and row[0]:
        try:
            decoded = base64.b64decode(row[0])
            entries = parse_proto(decoded)
            for _, _, entry_bytes in entries:
                entry_fields = parse_proto(entry_bytes)
                cid = None
                sub_bytes = None
                for fn, wt, val in entry_fields:
                    if fn == 1:
                        cid = val.decode("utf-8")
                    elif fn == 2:
                        sub_fields = parse_proto(val)
                        if sub_fields:
                            sub_bytes = base64.b64decode(sub_fields[0][2])
                if cid and sub_bytes:
                    existing_summaries[cid] = sub_bytes
        except Exception as e:
            if not quiet:
                console.print(f"[yellow]Warning: Failed to parse existing IDE summaries ({e}). Rebuilding...[/yellow]")

    # 2. Connect to CLI summaries DB
    if not quiet:
        console.print("[dim]Connecting to CLI summaries DB...[/dim]")
    cli_conn = get_sqlite_conn(CLI_SUMMARIES_DB)
    cli_curr = cli_conn.cursor()
    cli_curr.execute(
        """
        CREATE TABLE IF NOT EXISTS conversation_summaries (
            conversation_id TEXT PRIMARY KEY,
            title TEXT,
            step_count INTEGER,
            last_modified_time TEXT,
            workspace_uris TEXT,
            status TEXT,
            last_user_input_time TEXT
        )
        """
    )

    # 3. Discover active conversations (sorted newest first)
    db_files = [f for f in CONVS_DIR.glob("*.db") if f.name != "conversation_summaries.db"]
    db_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    if not quiet:
        console.print(f"[green]Found {len(db_files)} conversations on disk.[/green]")

    new_summaries_list = []
    synced_count = 0

    for db_path in db_files:
        cid = db_path.stem
        try:
            c_conn = get_sqlite_conn(db_path, timeout=5.0, readonly=True)
            c_curr = c_conn.cursor()
            try:
                step_count = c_curr.execute("SELECT COUNT(*) FROM steps").fetchone()[0]
            except sqlite3.OperationalError:
                step_count = 0
            c_conn.close()

            workspace = get_workspace_from_disk(cid, db_path)
            title = get_title_from_transcript(cid) or f"Session {cid[:6]}"

            now = db_path.stat().st_mtime
            time_str = datetime.fromtimestamp(now, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

            cli_curr.execute(
                """
                INSERT OR REPLACE INTO conversation_summaries
                (conversation_id, title, step_count, last_modified_time, workspace_uris, status, last_user_input_time)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (cid, title, step_count, time_str, workspace, "idle", time_str),
            )

            existing_info = existing_summaries.get(cid)
            new_info_bytes = build_ide_info_proto(cid, title, step_count, workspace, now, existing_info)

            info_b64 = base64.b64encode(new_info_bytes)
            sub_msg = encode_varint((1 << 3) | 2) + encode_varint(len(info_b64)) + info_b64
            entry_bytes = encode_string(1, cid) + encode_varint((2 << 3) | 2) + encode_varint(len(sub_msg)) + sub_msg

            new_summaries_list.append(entry_bytes)
            synced_count += 1
            if not quiet:
                console.print(f"  [dim]Processed:[/dim] [cyan]{cid[:8]}[/cyan] | Steps: {step_count:4d} | Title: {title[:45]}")

        except Exception as e:
            if not quiet:
                console.print(f"[red]Failed to sync conversation {cid[:8]}: {e}[/red]")

    cli_conn.commit()
    cli_conn.close()
    if not quiet:
        console.print(f"[bold green]✔ CLI Index Database updated ({synced_count} entries).[/bold green]")

    outer_bytes = bytearray()
    for entry in new_summaries_list:
        outer_bytes += encode_varint((1 << 3) | 2) + encode_varint(len(entry)) + entry

    final_b64 = base64.b64encode(outer_bytes).decode("utf-8")

    try:
        backup_sqlite_db(IDE_STATE_DB)
        ide_conn.execute(
            "INSERT OR REPLACE INTO ItemTable (key, value) VALUES ('antigravityUnifiedStateSync.trajectorySummaries', ?)",
            (final_b64,),
        )
        ide_conn.commit()
        if not quiet:
            console.print("[bold green]✔ IDE Global State Database updated (backup saved).[/bold green]")
    except Exception as e:
        console.print(f"[bold red]Failed to write to IDE Global State: {e}[/bold red]")
    finally:
        ide_conn.close()

    if ide_running_at_start or is_ide_running():
        console.print("\n[bold yellow]" + "=" * 70 + "[/bold yellow]")
        console.print("[bold yellow]⚠️  WARNING: Antigravity IDE is currently running![/bold yellow]")
        console.print("Changes written to disk will NOT appear in the UI while IDE is open,")
        console.print("and may be overwritten upon closing due to in-memory state caching.")
        console.print("Run [bold cyan]agx sync --restart[/bold cyan] to auto-restart IDE and apply.")
        console.print("[bold yellow]" + "=" * 70 + "[/bold yellow]\n")

    return 0


def execute_restart(force: bool = False) -> int:
    console.print("[bold cyan]Stopping Antigravity IDE...[/bold cyan]")
    if is_ide_running():
        stop_ide()
        console.print("[green]✔ IDE stopped cleanly.[/green]")
    else:
        console.print("[dim]IDE was not running.[/dim]")

    res = execute_sync(quiet=False, force=force)
    if res != 0:
        return res

    console.print("[bold cyan]Relaunching Antigravity IDE...[/bold cyan]")
    if start_ide():
        console.print("[bold green]✔ Antigravity IDE launched successfully.[/bold green]")
        return 0
    else:
        console.print("[bold red]Failed to launch Antigravity IDE executable.[/bold red]")
        return 1
