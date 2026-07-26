"""The lead store is a web-UI concern only -- these tests need no FastAPI."""

from __future__ import annotations

import sqlite3

from pitch_doctor.web.leads import count_leads, init_db, leads_path, save_lead


def test_leads_live_next_to_the_reports(tmp_path):
    assert leads_path(tmp_path) == tmp_path / "leads.db"


def test_init_is_idempotent(tmp_path):
    path = leads_path(tmp_path)
    init_db(path)
    init_db(path)
    assert count_leads(path) == 0


def test_saving_a_lead_records_every_field(tmp_path):
    path = leads_path(tmp_path)
    save_lead(
        path,
        email="owner@example.test",
        business_name="Joe's Plumbing",
        city="Houston",
        url="https://joesplumbing.test",
        score=54,
    )

    conn = sqlite3.connect(path)
    try:
        row = conn.execute(
            "SELECT email, business_name, city, url, score, created_at FROM leads"
        ).fetchone()
    finally:
        conn.close()

    assert row[:5] == (
        "owner@example.test",
        "Joe's Plumbing",
        "Houston",
        "https://joesplumbing.test",
        54,
    )
    assert row[5]  # created_at is stamped


def test_a_websiteless_lead_stores_a_null_url(tmp_path):
    path = leads_path(tmp_path)
    save_lead(
        path,
        email="owner@example.test",
        business_name="Corner Barber",
        city="Katy",
        url=None,
        score=0,
    )
    conn = sqlite3.connect(path)
    try:
        url, score = conn.execute("SELECT url, score FROM leads").fetchone()
    finally:
        conn.close()
    assert url is None
    assert score == 0


def test_leads_accumulate(tmp_path):
    path = leads_path(tmp_path)
    for i in range(3):
        save_lead(
            path,
            email=f"lead{i}@example.test",
            business_name=None,
            city=None,
            url="https://example.test",
            score=i,
        )
    assert count_leads(path) == 3


def test_a_broken_lead_store_never_breaks_a_scan(tmp_path):
    # Losing a lead row is bad; losing the report the visitor asked for is worse.
    blocker = tmp_path / "blocker"
    blocker.write_text("not a directory", encoding="utf-8")
    doomed = blocker / "nested" / "leads.db"

    save_lead(
        doomed,
        email="owner@example.test",
        business_name="Joe's Plumbing",
        city="Houston",
        url=None,
        score=0,
    )  # must not raise
    assert count_leads(doomed) == 0
