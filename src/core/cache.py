import sqlite3
from pathlib import Path


class HashCache:
    def __init__(self, db_path: Path):
        self.conn = sqlite3.connect(db_path)
        self._create_table()

    def _create_table(self) -> None:
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

    def get(self, path: Path) -> str | None:
        stat = path.stat()

        result = self.conn.execute(
            "SELECT hash, mtime, size FROM hashes WHERE path = ?",
            (str(path),),
        ).fetchone()

        if result is None:
            return None

        hash_value, mtime, size = result

        if mtime == stat.st_mtime and size == stat.st_size:
            return hash_value

        return None

    def set_many(self, entries: list[tuple[Path, str]]) -> None:
        rows = []

        for path, hash_value in entries:
            stat = path.stat()
            rows.append((str(path), stat.st_mtime, stat.st_size, hash_value))

        self.conn.executemany(
            """
            INSERT OR REPLACE INTO hashes (path, mtime, size, hash)
            VALUES (?, ?, ?, ?)
            """,
            rows,
        )
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()