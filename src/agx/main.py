"""
AGX - Antigravity Unified Management Suite
==========================================
Main CLI Application (Typer)
"""

from typing import Optional

import typer

from agx import __version__
from agx.commands.backup import execute_backup, execute_restore
from agx.commands.config_cmd import execute_config_init, execute_config_show
from agx.commands.dedup import execute_dedup
from agx.commands.diff import execute_diff
from agx.commands.doctor import execute_doctor
from agx.commands.export import execute_export
from agx.commands.list_cmd import execute_list
from agx.commands.prune import execute_prune
from agx.commands.rebind import execute_rebind
from agx.commands.search import execute_search
from agx.commands.stats import execute_stats
from agx.commands.sync import execute_restart, execute_sync
from agx.commands.watch import execute_watch

app = typer.Typer(
    name="agx",
    help="Antigravity CLI & IDE Unified Management Suite",
    add_completion=True,
    no_args_is_help=True,
)

config_app = typer.Typer(help="Manage AGX configuration file.")
app.add_typer(config_app, name="config")


@config_app.command("init")
def config_init_cmd(
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing configuration file"),
):
    """Initialize a new config.toml file in XDG config directory."""
    execute_config_init(force=force)


@config_app.command("show")
def config_show_cmd():
    """Display current configuration file path and contents."""
    execute_config_show()


def version_callback(value: bool):
    if value:
        typer.echo(f"agx {__version__}")
        raise typer.Exit()


@app.callback()
def main_callback(
    version: Optional[bool] = typer.Option(
        None,
        "-v",
        "--version",
        help="Show AGX version and exit.",
        callback=version_callback,
        is_eager=True,
    ),
):
    """Antigravity CLI & IDE Unified Management Suite."""
    pass


@app.command("sync")
def sync_command(
    restart: bool = typer.Option(False, "-r", "--restart", help="Terminate IDE, sync database, and relaunch IDE"),
    quiet: bool = typer.Option(False, "-q", "--quiet", help="Suppress routine output"),
    force: bool = typer.Option(False, "-f", "--force", help="Bypass target version locks"),
):
    """Synchronize conversation indexes between CLI and IDE."""
    if restart:
        execute_restart(force=force)
    else:
        execute_sync(quiet=quiet, force=force)


@app.command("list")
def list_command(
    limit: int = typer.Option(25, "-n", "--limit", help="Number of items to display"),
    workspace: Optional[str] = typer.Option(None, "-w", "--workspace", help="Filter by workspace URI"),
):
    """List recent conversations in table format."""
    execute_list(limit=limit, workspace=workspace)


@app.command("search")
def search_command(
    query: str = typer.Argument(..., help="Search query string"),
):
    """Full-text search across conversation titles and transcripts."""
    execute_search(query=query)


@app.command("stats")
def stats_command():
    """Display workspace usage analytics and step breakdowns."""
    execute_stats()


@app.command("diff")
def diff_command(
    cid1: str = typer.Argument(..., help="First conversation ID or prefix"),
    cid2: str = typer.Argument(..., help="Second conversation ID or prefix"),
):
    """Compare two conversation trajectories side-by-side."""
    execute_diff(cid1_raw=cid1, cid2_raw=cid2)


@app.command("dedup")
def dedup_command(
    apply: bool = typer.Option(False, "--apply", help="Apply cleanup and delete duplicate sessions"),
):
    """Detect and remove duplicate conversation sessions."""
    execute_dedup(apply=apply)


@app.command("rebind")
def rebind_command(
    old_path: str = typer.Argument(..., help="Old workspace path or URI"),
    new_path: str = typer.Argument(..., help="New workspace path or URI"),
):
    """Rebind conversation workspaces when projects are moved or renamed."""
    execute_rebind(old_path=old_path, new_path=new_path)


@app.command("prune")
def prune_command():
    """Prune orphaned index entries and delete dangling .tmp files."""
    execute_prune()


@app.command("backup")
def backup_command(
    output: Optional[str] = typer.Option(None, "-o", "--output", help="Output .tar.gz archive path"),
):
    """Create a complete state snapshot archive."""
    execute_backup(output_path=output)


@app.command("restore")
def restore_command(
    archive: str = typer.Argument(..., help="Path to backup .tar.gz archive"),
):
    """Restore conversation state from a backup archive."""
    execute_restore(archive_path=archive)


@app.command("export")
def export_command(
    cid: str = typer.Argument(..., help="Conversation ID or prefix"),
    output: Optional[str] = typer.Option(None, "-o", "--output", help="Output Markdown file path"),
):
    """Export conversation transcript as a clean Markdown document."""
    execute_export(cid_raw=cid, output_path=output)


@app.command("doctor")
def doctor_command():
    """Run diagnostic integrity health check."""
    execute_doctor()


@app.command("watch")
def watch_command(
    interval: int = typer.Option(5, "--interval", help="Polling interval in seconds"),
):
    """Run background watcher daemon for continuous auto-sync."""
    execute_watch(interval=interval)


if __name__ == "__main__":
    app()
