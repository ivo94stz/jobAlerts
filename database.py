import os
import sqlite3
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "seen_jobs.db")

_CREATE = """
CREATE TABLE IF NOT EXISTS seen_jobs (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    source    TEXT    NOT NULL,
    job_id    TEXT    NOT NULL,
    title     TEXT,
    company   TEXT,
    url       TEXT,
    found_at  TEXT    DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source, job_id)
)
"""


def _conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.execute(_CREATE)
    con.commit()
    return con


def is_seen(source: str, job_id: str) -> bool:
    with _conn() as con:
        row = con.execute(
            "SELECT 1 FROM seen_jobs WHERE source = ? AND job_id = ?",
            (source, job_id),
        ).fetchone()
    return row is not None


def mark_seen(source: str, job_id: str, title: str = "", company: str = "", url: str = ""):
    try:
        with _conn() as con:
            con.execute(
                """INSERT OR IGNORE INTO seen_jobs (source, job_id, title, company, url, found_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (source, job_id, title, company, url, datetime.utcnow().isoformat()),
            )
            con.commit()
    except Exception as e:
        print(f"[db] Failed to mark seen: {e}")
