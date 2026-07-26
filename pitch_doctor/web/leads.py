"""Lead capture for the web UI, and only for the web UI.

The scan engine deliberately knows nothing about this: the CLI must keep
working for a freelancer auditing prospects offline, where an email address is
neither available nor meaningful. Requiring one is purely a property of the
public web form, which trades a report for a contact.

Storage is a single SQLite file next to the reports. No email is sent from
here -- leads are only recorded.
"""

from __future__ import annotations

import datetime as dt
import sqlite3
from pathlib import Path

LEADS_FILENAME = "leads.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS leads (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    email         TEXT NOT NULL,
    business_name TEXT,
    city          TEXT,
    url           TEXT,
    score         INTEGER,
    created_at    TEXT NOT NULL
)
"""


def leads_path(out_dir: Path) -> Path:
    return out_dir / LEADS_FILENAME


def init_db(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    try:
        conn.execute(_SCHEMA)
        conn.commit()
    finally:
        conn.close()


def save_lead(
    path: Path,
    *,
    email: str,
    business_name: str | None,
    city: str | None,
    url: str | None,
    score: int | None,
) -> None:
    """Record one lead. Never raises: losing a lead row must not lose the report."""
    try:
        init_db(path)
        conn = sqlite3.connect(path)
    except (sqlite3.Error, OSError):
        # An unwritable path (bad directory, permissions, full disk) must not
        # cost the visitor the report they came for.
        return
    try:
        conn.execute(
            "INSERT INTO leads (email, business_name, city, url, score, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (
                email,
                business_name,
                city,
                url,
                score,
                dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
            ),
        )
        conn.commit()
    except sqlite3.Error:
        pass
    finally:
        conn.close()


def count_leads(path: Path) -> int:
    """How many leads are stored. Used by tests and by anyone poking at the file."""
    try:
        if not path.exists():
            return 0
        conn = sqlite3.connect(path)
    except (sqlite3.Error, OSError):
        return 0
    try:
        return conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
    except sqlite3.Error:
        return 0
    finally:
        conn.close()
