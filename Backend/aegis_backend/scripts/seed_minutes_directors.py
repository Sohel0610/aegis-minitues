#!/usr/bin/env python3
"""
Seed Minutes director tables for local / SQLite setups.

Why: local_fallback.db is gitignored (*.db). Other machines pull code but have
empty company_directors / external_board_members, so Attendance step shows nobody.

This script loads committed JSON seeds under public/seeds/ into the minutes DB.
It is idempotent and does not hardcode people — data comes from the seed files
(exported from the shared director registry).

Usage (from Backend/aegis_backend):
  python scripts/seed_minutes_directors.py
  python scripts/seed_minutes_directors.py --force   # clear & reload seed rows
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SEED_DIR = os.path.join(ROOT, "public", "seeds")
DB_PATH = os.path.join(ROOT, "public", "local_fallback.db")


def _connect():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_schema(cur: sqlite3.Cursor) -> None:
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS company_directors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT NOT NULL,
            name TEXT NOT NULL,
            din TEXT,
            designation TEXT DEFAULT 'Director',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    try:
        cur.execute("ALTER TABLE company_directors ADD COLUMN designation TEXT DEFAULT 'Director'")
    except Exception:
        pass

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS external_board_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            din TEXT NOT NULL,
            name TEXT,
            cin TEXT NOT NULL DEFAULT '',
            company_name TEXT,
            designation TEXT DEFAULT 'Director',
            appointment_date TEXT,
            status TEXT DEFAULT 'Active',
            source TEXT DEFAULT 'SEED',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(din, company_name)
        )
        """
    )


def seed_company_directors(cur: sqlite3.Cursor, force: bool) -> int:
    path = os.path.join(SEED_DIR, "minutes_company_directors.json")
    if not os.path.exists(path):
        print(f"SKIP company_directors — missing {path}")
        return 0

    count = cur.execute("SELECT COUNT(*) FROM company_directors").fetchone()[0]
    if count > 0 and not force:
        print(f"OK company_directors already has {count} rows (use --force to reload)")
        return 0

    with open(path, encoding="utf-8") as f:
        payload = json.load(f)
    rows = payload.get("directors") or []

    if force:
        cur.execute("DELETE FROM company_directors")

    inserted = 0
    for r in rows:
        company = (r.get("company_name") or "").strip()
        name = (r.get("name") or "").strip()
        if not company or not name:
            continue
        cur.execute(
            """
            INSERT INTO company_directors (company_name, name, din, designation)
            VALUES (?, ?, ?, ?)
            """,
            (
                company,
                name,
                (r.get("din") or "").strip(),
                (r.get("designation") or "Director").strip() or "Director",
            ),
        )
        inserted += 1
    print(f"Seeded company_directors: {inserted} rows")
    return inserted


def seed_external_board_members(cur: sqlite3.Cursor, force: bool) -> int:
    path = os.path.join(SEED_DIR, "minutes_external_board_members.json")
    if not os.path.exists(path):
        print(f"SKIP external_board_members — missing {path}")
        return 0

    count = cur.execute("SELECT COUNT(*) FROM external_board_members").fetchone()[0]
    if count > 0 and not force:
        print(f"OK external_board_members already has {count} rows (use --force to reload)")
        return 0

    with open(path, encoding="utf-8") as f:
        payload = json.load(f)
    rows = payload.get("members") or []

    if force:
        cur.execute("DELETE FROM external_board_members")

    inserted = 0
    for r in rows:
        company = (r.get("company_name") or "").strip()
        name = (r.get("name") or "").strip()
        din = (r.get("din") or "").strip()
        if not company or not name:
            continue
        try:
            cur.execute(
                """
                INSERT OR IGNORE INTO external_board_members
                    (din, name, cin, company_name, designation, appointment_date, status, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    din or f"SEED-{company}-{name}"[:40],
                    name,
                    (r.get("cin") or "").strip(),
                    company,
                    (r.get("designation") or "Director").strip() or "Director",
                    r.get("appointment_date"),
                    (r.get("status") or "Active"),
                    (r.get("source") or "SEED"),
                ),
            )
            inserted += 1
        except Exception as ex:
            print(f"  warn skip {name}@{company}: {ex}")
    print(f"Seeded external_board_members: {inserted} rows")
    return inserted


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed Minutes director tables")
    parser.add_argument("--force", action="store_true", help="Reload seed data even if tables have rows")
    args = parser.parse_args()

    print(f"DB: {DB_PATH}")
    print(f"Seeds: {SEED_DIR}")
    conn = _connect()
    try:
        cur = conn.cursor()
        _ensure_schema(cur)
        seed_external_board_members(cur, args.force)
        seed_company_directors(cur, args.force)
        conn.commit()
        ebm = cur.execute("SELECT COUNT(*) FROM external_board_members").fetchone()[0]
        cd = cur.execute("SELECT COUNT(*) FROM company_directors").fetchone()[0]
        print(f"Done. external_board_members={ebm}, company_directors={cd}")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
