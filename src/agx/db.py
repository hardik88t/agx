"""
SQLite Database Access & Backup Helpers
======================================
"""

import shutil
import sqlite3
from pathlib import Path
from typing import Optional


def get_sqlite_conn(db_path: Path, timeout: float = 10.0, readonly: bool = False) -> sqlite3.Connection:
    uri = f"file:{db_path}?mode=ro" if readonly else str(db_path)
    return sqlite3.connect(uri, timeout=timeout, uri=readonly)


def check_db_integrity(db_path: Path) -> str:
    if not db_path.exists():
        return "missing"
    try:
        conn = get_sqlite_conn(db_path, timeout=5.0, readonly=True)
        res = conn.execute("PRAGMA integrity_check").fetchone()[0]
        conn.close()
        return res
    except Exception as e:
        return f"error: {e}"


def backup_sqlite_db(source_path: Path, backup_suffix: str = ".sync-backup") -> Optional[Path]:
    if not source_path.exists():
        return None
    dest_path = source_path.with_name(f"{source_path.name}{backup_suffix}")
    try:
        shutil.copyfile(source_path, dest_path)
        return dest_path
    except Exception:
        return None
