import json
import os
import sqlite3
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "seen_jobs.db")

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


def export_to_json(path: str):
    """Export seen (source, job_id) pairs to JSON for cloud persistence."""
    with _conn() as con:
        rows = con.execute("SELECT source, job_id FROM seen_jobs").fetchall()
    data = [{"source": r[0], "job_id": r[1]} for r in rows]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)


def get_jobs_last_7_days() -> list:
    """Return all jobs found in the past 7 days for the weekly digest."""
    from datetime import timedelta
    cutoff = (datetime.utcnow() - timedelta(days=7)).isoformat()
    with _conn() as con:
        rows = con.execute(
            """SELECT title, company, url, source, found_at
               FROM seen_jobs
               WHERE found_at >= ? AND title != ''
               ORDER BY found_at DESC""",
            (cutoff,),
        ).fetchall()
    return [
        {"title": r[0], "company": r[1], "url": r[2], "source": r[3], "found_at": r[4]}
        for r in rows
    ]


def import_from_json(path: str):
    """Import seen job IDs from JSON into SQLite (used on cloud runner startup)."""
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        with _conn() as con:
            for item in data:
                con.execute(
                    "INSERT OR IGNORE INTO seen_jobs (source, job_id) VALUES (?, ?)",
                    (item["source"], item["job_id"]),
                )
            con.commit()
    except FileNotFoundError:
        pass  # First run — no file yet
