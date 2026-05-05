import json
import os
import re
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

_LEGAL_SUFFIXES = re.compile(
    r"\b(ag|gmbh|ltd|sa|llc|inc|corp|se|nv|bv|plc|srl|oy|ab|as)\b", re.I
)


def _normalize(text: str) -> str:
    text = (text or "").lower().strip()
    text = _LEGAL_SUFFIXES.sub("", text)
    text = re.sub(r"[^\w\s]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def _content_key(title: str, company: str) -> str:
    """Stable key used for cross-site deduplication."""
    return f"{_normalize(title)}||{_normalize(company)}"


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


def is_seen_by_content(title: str, company: str) -> bool:
    """Return True if a job with the same normalised title+company was already
    seen from *any* source.  Used to suppress cross-site duplicates across runs."""
    key = _content_key(title, company)
    if not key.replace("||", "").strip():
        return False
    with _conn() as con:
        row = con.execute(
            "SELECT 1 FROM seen_jobs WHERE content_key = ?", (key,)
        ).fetchone()
    return row is not None


def mark_seen(source: str, job_id: str, title: str = "", company: str = "", url: str = ""):
    try:
        key = _content_key(title, company)
        with _conn() as con:
            # Ensure content_key column exists (added after initial deploy)
            _ensure_content_key_column(con)
            con.execute(
                """INSERT OR IGNORE INTO seen_jobs
                       (source, job_id, title, company, url, found_at, content_key)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (source, job_id, title, company, url, datetime.utcnow().isoformat(), key),
            )
            con.commit()
    except Exception as e:
        print(f"[db] Failed to mark seen: {e}")


def _ensure_content_key_column(con: sqlite3.Connection) -> None:
    cols = {r[1] for r in con.execute("PRAGMA table_info(seen_jobs)").fetchall()}
    if "content_key" not in cols:
        con.execute("ALTER TABLE seen_jobs ADD COLUMN content_key TEXT")
        con.execute(
            "CREATE INDEX IF NOT EXISTS idx_content_key ON seen_jobs(content_key)"
        )
        con.commit()


def export_to_json(path: str):
    """Export seen jobs to JSON for cloud persistence.
    Includes title+company so cross-site dedup survives across runs."""
    with _conn() as con:
        rows = con.execute(
            "SELECT source, job_id, title, company FROM seen_jobs"
        ).fetchall()
    data = [
        {"source": r[0], "job_id": r[1], "title": r[2] or "", "company": r[3] or ""}
        for r in rows
    ]
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
            _ensure_content_key_column(con)
            for item in data:
                title = item.get("title", "")
                company = item.get("company", "")
                key = _content_key(title, company)
                con.execute(
                    """INSERT OR IGNORE INTO seen_jobs
                           (source, job_id, title, company, content_key)
                       VALUES (?, ?, ?, ?, ?)""",
                    (item["source"], item["job_id"], title, company, key),
                )
            con.commit()
    except FileNotFoundError:
        pass  # First run — no file yet
