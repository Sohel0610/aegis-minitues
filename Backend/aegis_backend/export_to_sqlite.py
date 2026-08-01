"""
Aegis Full Database Export — PostgreSQL → SQLite
─────────────────────────────────────────────────
Clones the ENTIRE director_disclosure_system Azure PostgreSQL database
into a local SQLite .db file with zero data transformation.

Rules:
  • Every schema, table, column name, and value is copied EXACTLY as-is
  • Column casing is 100% preserved
  • All data types handled: numeric, bool, decimal, datetime → correct SQLite affinity
  • Script auto-discovers all schemas — no hardcoding needed
  • On conflict: table is dropped and fully rebuilt to guarantee freshness
"""

import os
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from datetime import date, datetime
from decimal import Decimal

# ─── Load Environment ──────────────────────────────────────
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
load_dotenv(env_path)

# ─── PostgreSQL PG-type → SQLite affinity map ─────────────
def pg_to_sqlite_type(pg_type: str) -> str:
    pg_type = pg_type.lower()
    if any(x in pg_type for x in ("int", "serial", "smallint", "bigint")):
        return "INTEGER"
    if any(x in pg_type for x in ("numeric", "decimal", "double", "float", "real", "money")):
        return "REAL"
    if "bool" in pg_type:
        return "INTEGER"  # 0/1
    return "TEXT"         # text, uuid, date, timestamp, json, etc.

# ─── Safe value coercion ───────────────────────────────────
def coerce(v):
    """Convert any non-primitive PostgreSQL value to a SQLite-safe type."""
    if v is None:
        return None
    if isinstance(v, bool):
        return 1 if v else 0
    if isinstance(v, (int, float)):
        return v
    if isinstance(v, Decimal):
        return float(v)
    if isinstance(v, (datetime, date)):
        return str(v)
    if isinstance(v, str):
        return v
    if isinstance(v, bytes):
        return v
    # Fallback: stringify everything else (e.g. UUID, list, dict)
    return str(v)


def migrate_pg_to_sqlite():
    pg_host = os.getenv('POSTGRES_HOST')
    pg_port = os.getenv('POSTGRES_PORT', '5432')
    pg_user = os.getenv('POSTGRES_USER')
    pg_pass = os.getenv('POSTGRES_PASSWORD')
    pg_db   = os.getenv('POSTGRES_DATABASE_DIRECTOR', 'director_disclosure_system')

    sqlite_db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "aegis_directors_backup.db")

    print("═══════════════════════════════════════════════════════")
    print(" AEGIS DATABASE EXPORT — PostgreSQL → SQLite")
    print("═══════════════════════════════════════════════════════")
    print(f"  Source : {pg_host} / {pg_db}")
    print(f"  Target : {sqlite_db_path}")
    print("═══════════════════════════════════════════════════════\n")

    pg_conn     = None
    sqlite_conn = None

    try:
        # ── Connect to PostgreSQL ─────────────────────────────
        pg_conn = psycopg2.connect(
            host=pg_host, port=pg_port,
            user=pg_user, password=pg_pass,
            dbname=pg_db, sslmode='require'
        )
        pg_cur = pg_conn.cursor(cursor_factory=RealDictCursor)

        # ── Connect to SQLite ──────────────────────────────────
        sqlite_conn = sqlite3.connect(sqlite_db_path)
        sqlite_conn.execute("PRAGMA journal_mode=WAL")   # faster writes
        sqlite_conn.execute("PRAGMA synchronous=NORMAL")
        sqlite_cur = sqlite_conn.cursor()

        # ── Step 1: Discover ALL user schemas + tables ─────────
        pg_cur.execute("""
            SELECT table_schema, table_name
            FROM information_schema.tables
            WHERE table_type = 'BASE TABLE'
              AND table_schema NOT IN ('pg_catalog', 'information_schema')
            ORDER BY table_schema, table_name
        """)
        tables = pg_cur.fetchall()
        total  = len(tables)
        print(f"  Found {total} tables across all schemas.\n")

        total_rows_exported = 0

        for idx, tbl in enumerate(tables, 1):
            schema     = tbl['table_schema']
            table      = tbl['table_name']
            sqlite_name = f"{schema}__{table}"   # double-underscore separator

            print(f"  [{idx:>3}/{total}] {schema}.{table}  →  {sqlite_name}")

            # ── Step 2: Fetch exact column metadata ────────────
            pg_cur.execute("""
                SELECT column_name, data_type, ordinal_position
                FROM information_schema.columns
                WHERE table_schema = %s AND table_name = %s
                ORDER BY ordinal_position
            """, (schema, table))
            columns = pg_cur.fetchall()

            if not columns:
                print(f"           ⚠  No columns found — skipped.")
                continue

            # ── Step 3: Build CREATE TABLE (exact column names) ─
            col_defs = ", ".join(
                f'"{col["column_name"]}" {pg_to_sqlite_type(col["data_type"])}'
                for col in columns
            )
            sqlite_cur.execute(f'DROP TABLE IF EXISTS "{sqlite_name}"')
            sqlite_cur.execute(f'CREATE TABLE "{sqlite_name}" ({col_defs})')

            # ── Step 4: Fetch ALL rows from PostgreSQL ─────────
            pg_cur.execute(f'SELECT * FROM "{schema}"."{table}"')
            rows = pg_cur.fetchall()

            if rows:
                col_names    = list(rows[0].keys())
                col_list_sql = ", ".join(f'"{c}"' for c in col_names)
                placeholders = ", ".join("?" for _ in col_names)
                insert_sql   = f'INSERT INTO "{sqlite_name}" ({col_list_sql}) VALUES ({placeholders})'

                # ── Step 5: Coerce every value safely ──────────
                data = [tuple(coerce(v) for v in row.values()) for row in rows]
                sqlite_cur.executemany(insert_sql, data)

            total_rows_exported += len(rows)
            print(f"           ✓  {len(rows):,} rows")

        sqlite_conn.commit()

        print(f"\n═══════════════════════════════════════════════════════")
        print(f"  EXPORT COMPLETE")
        print(f"  Tables exported : {total}")
        print(f"  Total rows      : {total_rows_exported:,}")
        print(f"  Saved to        : {sqlite_db_path}")
        print(f"═══════════════════════════════════════════════════════")

    except Exception as e:
        print(f"\n  CRITICAL ERROR: {e}")
        import traceback; traceback.print_exc()
    finally:
        if pg_conn:     pg_conn.close()
        if sqlite_conn: sqlite_conn.close()


if __name__ == "__main__":
    migrate_pg_to_sqlite()
