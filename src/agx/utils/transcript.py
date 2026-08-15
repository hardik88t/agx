"""
Transcript & Log Parsers
=======================
"""

import json
import re
import sqlite3
from pathlib import Path
from typing import Optional

from agx.config import BRAIN_DIR, CONVS_DIR, HOME


def clean_title_text(text: str) -> Optional[str]:
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    text = text.replace("\n", " ").replace("\r", " ").replace("\t", " ")
    text = re.sub(r"\s+", " ", text).strip()

    # Iteratively strip conversational greetings, filler, and command prefixes
    changed = True
    while changed:
        before = text
        text = re.sub(r"^(ok|so|now|and|hey|hi|hello)[, ]+", "", text, flags=re.IGNORECASE).strip()
        text = re.sub(
            r"^(can you |could you |please |help me |write |create |build |fix |update |explain )+",
            "",
            text,
            flags=re.IGNORECASE,
        ).strip()
        changed = text != before

    if len(text) > 3:
        text = text[0].upper() + text[1:]
        return text[:60] + "..." if len(text) > 60 else text
    return None


def get_title_from_transcript(cid: str) -> Optional[str]:
    log_path = BRAIN_DIR / cid / ".system_generated" / "logs" / "transcript.jsonl"
    if not log_path.exists():
        return None
    try:
        with open(log_path, "r", errors="ignore", encoding="utf-8") as f:
            for _ in range(15):
                line = f.readline()
                if not line:
                    break
                try:
                    data = json.loads(line)
                except Exception:
                    continue

                content = data.get("content", "")
                match = re.search(r"<USER_REQUEST>\s*(.*?)\s*</USER_REQUEST>", content, re.DOTALL | re.IGNORECASE)
                if match:
                    title = clean_title_text(match.group(1))
                    if title:
                        return title

                msg_type = data.get("type", "")
                source = data.get("source", "")
                if (msg_type == "USER_INPUT" or source == "USER_EXPLICIT") and content:
                    title = clean_title_text(content)
                    if title:
                        return title
    except Exception:
        pass
    return None


def get_workspace_from_disk(cid: str, db_path: Path) -> str:
    workspace = ""
    try:
        c_conn = sqlite3.connect(str(db_path), timeout=5.0)
        c_curr = c_conn.cursor()
        c_curr.execute("SELECT data FROM trajectory_metadata_blob WHERE id='main'")
        blob_row = c_curr.fetchone()
        if blob_row and blob_row[0]:
            blob = blob_row[0]
            f_idx = blob.find(b"file://")
            if f_idx != -1:
                end_clean = f_idx
                while end_clean < len(blob) and blob[end_clean] >= 32:
                    end_clean += 1
                workspace = blob[f_idx:end_clean].decode("utf-8", errors="ignore").strip()
        c_conn.close()
    except Exception:
        pass

    if not workspace:
        overview_path = BRAIN_DIR / cid / ".system_generated" / "logs" / "overview.txt"
        if overview_path.exists():
            try:
                with open(overview_path, "r", errors="ignore", encoding="utf-8") as of:
                    txt = of.read(4096)
                    m = re.search(r"file:///[^\s\"'>]+", txt)
                    if m:
                        workspace = m.group(0)
            except Exception:
                pass

    return workspace or f"file://{HOME}"


def resolve_cid(cid_prefix: str) -> str:
    cid_prefix = cid_prefix.strip()
    if (CONVS_DIR / f"{cid_prefix}.db").exists():
        return cid_prefix
    matches = list(CONVS_DIR.glob(f"{cid_prefix}*.db"))
    if matches:
        return matches[0].stem
    return cid_prefix
