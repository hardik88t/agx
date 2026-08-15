"""
Export Conversation to Markdown
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from rich.console import Console

from agx.config import BRAIN_DIR, CONVS_DIR
from agx.utils.transcript import get_title_from_transcript, get_workspace_from_disk, resolve_cid

console = Console()


def execute_export(cid_raw: str, output_path: Optional[str] = None):
    cid = resolve_cid(cid_raw)
    log_path = BRAIN_DIR / cid / ".system_generated" / "logs" / "transcript.jsonl"

    if not log_path.exists():
        console.print(f"[bold red]ERROR: No transcript found for conversation ID '{cid}'.[/bold red]")
        return

    title = get_title_from_transcript(cid) or f"Conversation {cid[:8]}"
    db_path = CONVS_DIR / f"{cid}.db"
    workspace = get_workspace_from_disk(cid, db_path) if db_path.exists() else "Unknown"

    lines = [
        f"# {title}\n",
        f"- **Conversation ID**: `{cid}`",
        f"- **Workspace**: `{workspace}`",
        f"- **Export Date**: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`\n",
        "---\n",
    ]

    with open(log_path, "r", errors="ignore", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                msg = json.loads(line)
                source = msg.get("source", "UNKNOWN")
                msg_type = msg.get("type", "")
                content = msg.get("content", "")

                if msg_type == "USER_INPUT" or source == "USER_EXPLICIT":
                    lines.append(f"### 👤 User\n\n{content}\n")
                elif msg_type == "PLANNER_RESPONSE" or source == "MODEL":
                    if content:
                        lines.append(f"### 🤖 Assistant\n\n{content}\n")
            except Exception:
                pass

    out_text = "\n".join(lines)
    if output_path:
        Path(output_path).write_text(out_text, encoding="utf-8")
        console.print(f"[bold green]✔ Conversation exported to:[/bold green] {output_path}")
    else:
        print(out_text)
