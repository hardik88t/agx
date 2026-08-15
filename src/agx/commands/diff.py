"""
Trajectory Diff Command
"""

import json
import re

from rich.console import Console
from rich.table import Table

from agx.config import BRAIN_DIR, CONVS_DIR
from agx.utils.transcript import get_title_from_transcript, get_workspace_from_disk, resolve_cid

console = Console()


def execute_diff(cid1_raw: str, cid2_raw: str):
    cid1 = resolve_cid(cid1_raw)
    cid2 = resolve_cid(cid2_raw)

    db1 = CONVS_DIR / f"{cid1}.db"
    db2 = CONVS_DIR / f"{cid2}.db"

    if not db1.exists() or not db2.exists():
        console.print(f"[bold red]ERROR: One or both conversations not found ({cid1[:8]}, {cid2[:8]}).[/bold red]")
        return

    t1 = get_title_from_transcript(cid1) or cid1[:8]
    t2 = get_title_from_transcript(cid2) or cid2[:8]

    ws1 = get_workspace_from_disk(cid1, db1)
    ws2 = get_workspace_from_disk(cid2, db2)

    def get_steps_and_prompts(cid: str):
        log_path = BRAIN_DIR / cid / ".system_generated" / "logs" / "transcript.jsonl"
        prompts = []
        step_count = 0
        if log_path.exists():
            try:
                with open(log_path, "r", errors="ignore", encoding="utf-8") as f:
                    for line in f:
                        if not line.strip():
                            continue
                        msg = json.loads(line)
                        step_count += 1
                        if msg.get("type") == "USER_INPUT" or msg.get("source") == "USER_EXPLICIT":
                            c = msg.get("content", "").strip()
                            m = re.search(r"<USER_REQUEST>\s*(.*?)\s*</USER_REQUEST>", c, re.DOTALL | re.IGNORECASE)
                            prompts.append(m.group(1).strip() if m else c[:80])
            except Exception:
                pass
        return step_count, prompts

    s1, p1 = get_steps_and_prompts(cid1)
    s2, p2 = get_steps_and_prompts(cid2)

    table = Table(title="Conversation Trajectory Diff", show_header=True, header_style="bold magenta")
    table.add_column("Property", style="bold")
    table.add_column(f"Session A ({cid1[:8]})", style="cyan")
    table.add_column(f"Session B ({cid2[:8]})", style="green")

    table.add_row("Title", t1, t2)
    table.add_row("Steps", str(s1), str(s2))
    table.add_row("Workspace", ws1, ws2)
    table.add_row("User Turns", str(len(p1)), str(len(p2)))
    console.print(table)

    console.print("\n[bold]• User Prompt Sequence Comparison:[/bold]")
    max_turns = max(len(p1), len(p2))
    for i in range(min(max_turns, 10)):
        u1 = p1[i] if i < len(p1) else "[No turn]"
        u2 = p2[i] if i < len(p2) else "[No turn]"
        u1 = (u1[:35] + "..") if len(u1) > 37 else u1
        u2 = (u2[:35] + "..") if len(u2) > 37 else u2
        console.print(f"  Turn {i+1:2d} -> A: [cyan]{u1:<38}[/cyan] | B: [green]{u2}[/green]")
    if max_turns > 10:
        console.print(f"  [dim]... ({max_turns - 10} more turns)[/dim]")
