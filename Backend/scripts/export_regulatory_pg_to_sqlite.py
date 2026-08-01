#!/usr/bin/env python3
"""
Export RBI, BSE, and SEBI notification data from PostgreSQL into one SQLite DB.

Run from the VM/repo root:
    python Backend/scripts/export_regulatory_pg_to_sqlite.py

By default this writes:
    ./sqlite.db

It reads PostgreSQL credentials from Backend/aegis_backend/.env or the current
environment:
    POSTGRES_HOST
    POSTGRES_PORT
    POSTGRES_USER
    POSTGRES_PASSWORD
    POSTGRES_SSLMODE
    POSTGRES_DATABASE_BSE
    POSTGRES_DATABASE_SEBI
    POSTGRES_DATABASE_RBI
"""

from __future__ import annotations

import argparse
import logging
import os
import sqlite3
import sys
from contextlib import closing
from pathlib import Path
from typing import Any, Iterable, Mapping

import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor


REPO_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = REPO_ROOT / "Backend" / "aegis_backend" / ".env"
DEFAULT_OUTPUT = REPO_ROOT / "sqlite.db"

LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"


TABLE_DEFINITIONS = {
    "bse_daily_logs": """
        CREATE TABLE bse_daily_logs (
            id INTEGER,
            sr_no INTEGER,
            entity_name TEXT,
            link TEXT,
            nature TEXT,
            summary TEXT,
            record_date TEXT
        )
    """,
    "sebi_excel_summaries": """
        CREATE TABLE sebi_excel_summaries (
            id INTEGER,
            date_key TEXT,
            row_index INTEGER,
            pdf_link TEXT,
            summary TEXT,
            inserted_at TEXT
        )
    """,
    "rbi_master_summaries": """
        CREATE TABLE rbi_master_summaries (
            id INTEGER,
            run_date TEXT,
            pdf_link TEXT,
            summary TEXT,
            created_at TEXT
        )
    """,
    "regulatory_notifications": """
        CREATE TABLE regulatory_notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            source_id INTEGER,
            date_key TEXT,
            row_index INTEGER,
            pdf_link TEXT,
            summary TEXT,
            inserted_at TEXT,
            entity_name TEXT,
            nature TEXT
        )
    """,
}


INDEX_DEFINITIONS = [
    "CREATE INDEX idx_bse_daily_logs_record_date ON bse_daily_logs(record_date)",
    "CREATE INDEX idx_bse_daily_logs_entity_name ON bse_daily_logs(entity_name)",
    "CREATE INDEX idx_sebi_excel_summaries_date_key ON sebi_excel_summaries(date_key)",
    "CREATE INDEX idx_rbi_master_summaries_run_date ON rbi_master_summaries(run_date)",
    "CREATE INDEX idx_regulatory_notifications_source ON regulatory_notifications(source)",
    "CREATE INDEX idx_regulatory_notifications_date_key ON regulatory_notifications(date_key)",
    "CREATE INDEX idx_regulatory_notifications_entity_name ON regulatory_notifications(entity_name)",
]


EXPORTS = {
    "bse": {
        "env": "POSTGRES_DATABASE_BSE",
        "table": "bse_daily_logs",
        "sql": """
            SELECT id, sr_no, entity_name, link, nature, summary, record_date::text AS record_date
            FROM daily_logs
            WHERE link IS NOT NULL
              AND link != 'NIL'
            ORDER BY record_date DESC, id ASC
        """,
        "columns": ["id", "sr_no", "entity_name", "link", "nature", "summary", "record_date"],
    },
    "sebi": {
        "env": "POSTGRES_DATABASE_SEBI",
        "fallback_env": "POSTGRES_DATABASE_BSE",
        "table": "sebi_excel_summaries",
        "source_tables": [
            {
                "name": "excel_summaries",
                "sql": """
                    SELECT id, date_key::text AS date_key, row_index, pdf_link, summary, inserted_at::text AS inserted_at
                    FROM excel_summaries
                    ORDER BY date_key DESC, row_index ASC
                """,
            },
            {
                "name": "aegis_sebi_data",
                "sql": """
                    SELECT id, date_key::text AS date_key, row_index, pdf_link, summary, inserted_at::text AS inserted_at
                    FROM aegis_sebi_data
                    ORDER BY date_key DESC, row_index ASC
                """,
            },
        ],
        "columns": ["id", "date_key", "row_index", "pdf_link", "summary", "inserted_at"],
    },
    "rbi": {
        "env": "POSTGRES_DATABASE_RBI",
        "table": "rbi_master_summaries",
        "sql": """
            SELECT id, run_date::text AS run_date, pdf_link, summary, created_at::text AS created_at
            FROM master_summaries
            WHERE NOT (pdf_link = 'NIL' AND summary = 'NIL')
            ORDER BY run_date DESC, id ASC
        """,
        "columns": ["id", "run_date", "pdf_link", "summary", "created_at"],
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export RBI/BSE/SEBI PostgreSQL notification data into a SQLite database."
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT),
        help=f"SQLite DB output path. Default: {DEFAULT_OUTPUT}",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=1000,
        help="Rows to copy per batch. Default: 1000",
    )
    parser.add_argument(
        "--keep-partial",
        action="store_true",
        help="Keep the temporary SQLite file if export fails.",
    )
    return parser.parse_args()


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def database_for(export_name: str, config: Mapping[str, Any]) -> str:
    database = os.getenv(config["env"])
    if not database and config.get("fallback_env"):
        database = os.getenv(config["fallback_env"])
    if not database:
        raise RuntimeError(f"Missing database env var for {export_name}: {config['env']}")
    return database


def pg_connect(database: str):
    params = {
        "host": require_env("POSTGRES_HOST"),
        "port": int(os.getenv("POSTGRES_PORT", "5432")),
        "user": require_env("POSTGRES_USER"),
        "password": require_env("POSTGRES_PASSWORD"),
        "database": database,
        "connect_timeout": 20,
    }

    sslmode = os.getenv("POSTGRES_SSLMODE")
    if sslmode:
        params["sslmode"] = sslmode
    elif "azure.com" in params["host"].lower():
        params["sslmode"] = "require"

    return psycopg2.connect(**params)


def table_exists(pg_conn, table_name: str) -> bool:
    with pg_conn.cursor() as cursor:
        cursor.execute("SELECT to_regclass(%s)", (table_name,))
        row = cursor.fetchone()
    return bool(row and row[0])


def select_export_sql(pg_conn, source: str, config: Mapping[str, Any]) -> tuple[str, str | None]:
    if config.get("source_tables"):
        for table_config in config["source_tables"]:
            if table_exists(pg_conn, table_config["name"]):
                return table_config["sql"], table_config["name"]

        table_names = ", ".join(table_config["name"] for table_config in config["source_tables"])
        raise RuntimeError(
            f"No supported source table found for {source.upper()}. Checked: {table_names}"
        )

    return config["sql"], None


def setup_sqlite(conn: sqlite3.Connection) -> None:
    conn.execute("PRAGMA journal_mode = DELETE")
    conn.execute("PRAGMA synchronous = NORMAL")
    conn.execute("PRAGMA foreign_keys = ON")

    for table in TABLE_DEFINITIONS:
        conn.execute(f"DROP TABLE IF EXISTS {table}")
    for ddl in TABLE_DEFINITIONS.values():
        conn.execute(ddl)


def insert_rows(
    sqlite_conn: sqlite3.Connection,
    table: str,
    columns: list[str],
    rows: Iterable[Mapping[str, Any]],
) -> int:
    placeholders = ", ".join(["?"] * len(columns))
    column_list = ", ".join(columns)
    sql = f"INSERT INTO {table} ({column_list}) VALUES ({placeholders})"

    values = [tuple(row.get(column) for column in columns) for row in rows]
    if not values:
        return 0

    sqlite_conn.executemany(sql, values)
    return len(values)


def insert_normalized(sqlite_conn: sqlite3.Connection, source: str, rows: list[Mapping[str, Any]]) -> int:
    normalized_rows = []
    for row in rows:
        if source == "bse":
            normalized_rows.append(
                {
                    "source": "BSE",
                    "source_id": row.get("id"),
                    "date_key": row.get("record_date"),
                    "row_index": row.get("sr_no"),
                    "pdf_link": row.get("link"),
                    "summary": row.get("summary"),
                    "inserted_at": row.get("record_date"),
                    "entity_name": row.get("entity_name"),
                    "nature": row.get("nature"),
                }
            )
        elif source == "sebi":
            normalized_rows.append(
                {
                    "source": "SEBI",
                    "source_id": row.get("id"),
                    "date_key": row.get("date_key"),
                    "row_index": row.get("row_index"),
                    "pdf_link": row.get("pdf_link"),
                    "summary": row.get("summary"),
                    "inserted_at": row.get("inserted_at"),
                    "entity_name": None,
                    "nature": None,
                }
            )
        elif source == "rbi":
            normalized_rows.append(
                {
                    "source": "RBI",
                    "source_id": row.get("id"),
                    "date_key": row.get("run_date"),
                    "row_index": row.get("id"),
                    "pdf_link": row.get("pdf_link"),
                    "summary": row.get("summary"),
                    "inserted_at": row.get("created_at"),
                    "entity_name": None,
                    "nature": None,
                }
            )

    return insert_rows(
        sqlite_conn,
        "regulatory_notifications",
        [
            "source",
            "source_id",
            "date_key",
            "row_index",
            "pdf_link",
            "summary",
            "inserted_at",
            "entity_name",
            "nature",
        ],
        normalized_rows,
    )


def export_dataset(
    sqlite_conn: sqlite3.Connection,
    source: str,
    config: Mapping[str, Any],
    batch_size: int,
) -> int:
    database = database_for(source, config)
    logging.info("Exporting %s from Postgres database %s", source.upper(), database)

    copied = 0
    with closing(pg_connect(database)) as pg_conn:
        export_sql, source_table = select_export_sql(pg_conn, source, config)
        if source_table:
            logging.info("Using %s source table: %s", source.upper(), source_table)

        with pg_conn.cursor(name=f"{source}_export_cursor", cursor_factory=RealDictCursor) as cursor:
            cursor.itersize = batch_size
            cursor.execute(export_sql)

            while True:
                rows = cursor.fetchmany(batch_size)
                if not rows:
                    break

                insert_rows(sqlite_conn, config["table"], config["columns"], rows)
                insert_normalized(sqlite_conn, source, rows)
                copied += len(rows)
                logging.info("Copied %s %s rows", copied, source.upper())

    return copied


def create_indexes(conn: sqlite3.Connection) -> None:
    for ddl in INDEX_DEFINITIONS:
        conn.execute(ddl)


def main() -> int:
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)

    load_dotenv(ENV_PATH)

    output_path = Path(args.output).expanduser()
    if not output_path.is_absolute():
        output_path = (Path.cwd() / output_path).resolve()
    temp_path = output_path.with_name(f"{output_path.name}.{os.getpid()}.tmp")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    counts: dict[str, int] = {}
    try:
        with closing(sqlite3.connect(temp_path)) as sqlite_conn:
            setup_sqlite(sqlite_conn)

            for source, config in EXPORTS.items():
                counts[source] = export_dataset(sqlite_conn, source, config, args.batch_size)
                sqlite_conn.commit()

            create_indexes(sqlite_conn)
            sqlite_conn.execute(
                "CREATE TABLE export_metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)"
            )
            sqlite_conn.executemany(
                "INSERT INTO export_metadata (key, value) VALUES (?, ?)",
                [
                    ("bse_rows", str(counts.get("bse", 0))),
                    ("sebi_rows", str(counts.get("sebi", 0))),
                    ("rbi_rows", str(counts.get("rbi", 0))),
                    ("output_path", str(output_path)),
                ],
            )
            sqlite_conn.commit()

        temp_path.replace(output_path)

    except Exception:
        logging.exception("Export failed")
        if temp_path.exists() and not args.keep_partial:
            try:
                temp_path.unlink()
            except PermissionError:
                logging.warning(
                    "Could not delete partial SQLite file because Windows still has it open: %s",
                    temp_path,
                )
        return 1

    logging.info("SQLite export completed: %s", output_path)
    logging.info(
        "Rows exported: BSE=%s, SEBI=%s, RBI=%s",
        counts.get("bse", 0),
        counts.get("sebi", 0),
        counts.get("rbi", 0),
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
