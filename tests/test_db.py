import tempfile
from pathlib import Path

from agx.db import backup_sqlite_db, check_db_integrity, get_sqlite_conn


def test_sqlite_conn_and_integrity():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        conn = get_sqlite_conn(db_path)
        conn.execute("CREATE TABLE foo (id INTEGER PRIMARY KEY, name TEXT)")
        conn.execute("INSERT INTO foo VALUES (1, 'bar')")
        conn.commit()
        conn.close()

        assert check_db_integrity(db_path) == "ok"

        # Test backup
        backup_path = backup_sqlite_db(db_path, backup_suffix=".bak")
        assert backup_path is not None
        assert backup_path.exists()
        assert backup_path.name == "test.db.bak"
