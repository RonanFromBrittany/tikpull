"""SQLite database for tikpull download history."""

from pathlib import Path

import aiosqlite

DB_DIR = Path.home() / ".local" / "share" / "tikpull"
DB_PATH = DB_DIR / "history.db"

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS downloads (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    url           TEXT NOT NULL,
    status        TEXT NOT NULL CHECK(status IN ('success', 'error', 'already_downloaded')),
    output_path   TEXT,
    error         TEXT,
    downloaded_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S', 'now'))
);
"""


async def init_db() -> None:
    """Create the database and table if they don't exist."""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(CREATE_TABLE_SQL)
        await db.commit()


async def record_download(
    url: str,
    status: str,
    output_path: str | None = None,
    error: str | None = None,
) -> None:
    """Insert a download record into the history table."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO downloads (url, status, output_path, error)
            VALUES (?, ?, ?, ?)
            """,
            (url, status, output_path, error),
        )
        await db.commit()


async def get_history(limit: int = 200) -> list[dict]:
    """Return the most recent download records, newest first."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT id, url, status, output_path, error, downloaded_at
            FROM downloads
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def clear_history() -> None:
    """Delete all records from the history table."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM downloads")
        await db.commit()
