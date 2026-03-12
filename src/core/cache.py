import sqlite3
from pathlib import Path


class HashCache:

    def __init__(self, db_path: Path):
        self.conn = sqlite3.connect(db_path)
        self._create_table()

    def _create_table(self):
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS hashes (
                path TEXT PRIMARY KEY,
                mtime REAL,
                size INTEGER,
                hash TEXT
            )
            """
        )
        self.conn.commit()

    def get(self, path: Path):

        stat = path.stat()

        result = self.conn.execute(
            "SELECT hash, mtime, size FROM hashes WHERE path=?",
            (str(path),),
        ).fetchone()

        if result is None:
            return None

        hash_value, mtime, size = result

        if mtime == stat.st_mtime and size == stat.st_size:
            return hash_value

        return None

    def set(self, path: Path, hash_value: str):

        stat = path.stat()

        self.conn.execute(
            """
            INSERT OR REPLACE INTO hashes(path, mtime, size, hash)
            VALUES (?, ?, ?, ?)
            """,
            (str(path), stat.st_mtime, stat.st_size, hash_value),
        )

        self.conn.commit()