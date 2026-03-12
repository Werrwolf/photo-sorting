import sqlite3
from pathlib import Path


class HashCache:
    def __init__(self, db_path: Path):
        self.conn = sqlite3.connect(db_path)
        self._create_tables()

    def _create_tables(self) -> None:
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS perceptual_hashes (
                path TEXT PRIMARY KEY,
                mtime REAL,
                size INTEGER,
                hash TEXT
            )
            """
        )
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS file_hashes (
                path TEXT PRIMARY KEY,
                mtime REAL,
                size INTEGER,
                hash TEXT
            )
            """
        )
        self.conn.commit()

    def _get_cached_hash(self, table: str, path: Path) -> str | None:
        stat = path.stat()

        result = self.conn.execute(
            f"SELECT hash, mtime, size FROM {table} WHERE path = ?",
            (str(path),),
        ).fetchone()

        if result is None:
            return None

        hash_value, mtime, size = result

        if mtime == stat.st_mtime and size == stat.st_size:
            return hash_value

        return None

    def _set_many(self, table: str, entries: list[tuple[Path, str]]) -> None:
        rows = []

        for path, hash_value in entries:
            stat = path.stat()
            rows.append((str(path), stat.st_mtime, stat.st_size, hash_value))

        self.conn.executemany(
            f"""
            INSERT OR REPLACE INTO {table} (path, mtime, size, hash)
            VALUES (?, ?, ?, ?)
            """,
            rows,
        )
        self.conn.commit()

    def get_perceptual_hash(self, path: Path) -> str | None:
        return self._get_cached_hash("perceptual_hashes", path)

    def set_many_perceptual_hashes(self, entries: list[tuple[Path, str]]) -> None:
        self._set_many("perceptual_hashes", entries)

    def get_file_hash(self, path: Path) -> str | None:
        return self._get_cached_hash("file_hashes", path)

    def set_many_file_hashes(self, entries: list[tuple[Path, str]]) -> None:
        self._set_many("file_hashes", entries)

    def close(self) -> None:
        self.conn.close()