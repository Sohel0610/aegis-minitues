"""
SSO Database Explorer
=====================
Connects to the AEGIS RBAC PostgreSQL database and dumps a full detailed report
into sso_db_output.md — covering schema, tables, columns, types, constraints,
indexes, row counts, and sample data (up to 4 rows per table).

Run:  python explore_sso_db.py
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import os

# ─────────────────────────────────────────────────────────
# Connection Credentials (from .env)
# ─────────────────────────────────────────────────────────
DB_CONFIG = {
    "host":     "az10psqldmrcbtp01.postgres.database.azure.com",
    "port":     5432,
    "user":     "psqladmin",
    "password": "1k8h02grUu+qJ2uHZb<{lB3LF%+Yj-Ar",
    "database": "visit_tracking_system",
    "sslmode":  "require",
    "connect_timeout": 15,
}

OUTPUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sso_db_output.md")
TARGET_SCHEMA = "rbac"


# ─────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────

def md_table(headers: list, rows: list) -> str:
    """Render a markdown table from a header list and list-of-list rows."""
    if not headers:
        return "_No columns_\n"
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))

    def fmt_row(cells):
        return "| " + " | ".join(str(c).ljust(col_widths[i]) for i, c in enumerate(cells)) + " |"

    separator = "| " + " | ".join("-" * w for w in col_widths) + " |"
    lines = [fmt_row(headers), separator] + [fmt_row(row) for row in rows]
    return "\n".join(lines) + "\n"


def safe_str(val):
    """Convert any value to a markdown-safe string."""
    if val is None:
        return "_NULL_"
    s = str(val)
    # Truncate long values
    if len(s) > 80:
        s = s[:77] + "..."
    # Escape pipe chars that break MD tables
    return s.replace("|", "\\|").replace("\n", " ").replace("\r", "")


# ─────────────────────────────────────────────────────────
# Main Explorer
# ─────────────────────────────────────────────────────────

def explore(conn) -> str:
    """Run all exploration queries and return the full markdown report."""
    cur = conn.cursor(cursor_factory=RealDictCursor)
    lines = []

    # ── Header ────────────────────────────────────────────
    lines.append(f"# SSO Database Exploration Report")
    lines.append(f"\n**Generated at:** `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`")
    lines.append(f"**Host:** `{DB_CONFIG['host']}`")
    lines.append(f"**Database:** `{DB_CONFIG['database']}`")
    lines.append(f"**Schema:** `{TARGET_SCHEMA}`")
    lines.append(f"**SSL:** `{DB_CONFIG['sslmode']}`\n")
    lines.append("---\n")

    # ── 1. PostgreSQL Server Info ──────────────────────────
    lines.append("## 1. PostgreSQL Server Info\n")
    cur.execute("SELECT version(), current_database(), current_user, pg_postmaster_start_time() AS started_at, inet_server_addr() AS server_ip, inet_server_port() AS server_port")
    info = cur.fetchone()
    lines.append(md_table(
        ["Field", "Value"],
        [
            ["Version",    safe_str(info["version"])],
            ["Database",   safe_str(info["current_database"])],
            ["User",       safe_str(info["current_user"])],
            ["Started At", safe_str(info["started_at"])],
            ["Server IP",  safe_str(info["server_ip"])],
            ["Port",       safe_str(info["server_port"])],
        ]
    ))

    # ── 2. All Schemas ─────────────────────────────────────
    lines.append("\n## 2. All Schemas in Database\n")
    cur.execute("""
        SELECT schema_name, schema_owner
        FROM information_schema.schemata
        ORDER BY schema_name
    """)
    schemas = cur.fetchall()
    rows = [[safe_str(r["schema_name"]), safe_str(r["schema_owner"])] for r in schemas]
    lines.append(md_table(["Schema Name", "Owner"], rows))

    # ── 3. All Tables in RBAC Schema ──────────────────────
    lines.append(f"\n## 3. All Tables in `{TARGET_SCHEMA}` Schema\n")
    cur.execute("""
        SELECT table_name,
               pg_size_pretty(pg_total_relation_size(quote_ident(%s)||'.'||quote_ident(table_name))) AS total_size
        FROM information_schema.tables
        WHERE table_schema = %s
          AND table_type   = 'BASE TABLE'
        ORDER BY table_name
    """, (TARGET_SCHEMA, TARGET_SCHEMA))
    tables = cur.fetchall()

    if not tables:
        lines.append(f"> ⚠️ No tables found in schema `{TARGET_SCHEMA}`. The schema may not be initialized yet.\n")
        return "\n".join(lines)

    table_names = [r["table_name"] for r in tables]
    rows = [[safe_str(r["table_name"]), safe_str(r["total_size"])] for r in tables]
    lines.append(md_table(["Table Name", "Size on Disk"], rows))

    # ── 4. Per-Table Deep Dive ─────────────────────────────
    lines.append(f"\n## 4. Table-by-Table Deep Dive\n")

    for tname in table_names:
        full_table = f"{TARGET_SCHEMA}.{tname}"
        lines.append(f"---\n\n### 4.x `{full_table}`\n")

        # 4a. Row count
        cur.execute(f"SELECT COUNT(*) AS cnt FROM {full_table}")
        row_count = cur.fetchone()["cnt"]
        lines.append(f"**Total Rows:** `{row_count}`\n")

        # 4b. Column info
        lines.append(f"\n#### Columns & Types\n")
        cur.execute("""
            SELECT
                c.column_name,
                c.data_type,
                c.udt_name,
                c.character_maximum_length,
                c.is_nullable,
                c.column_default,
                c.ordinal_position
            FROM information_schema.columns c
            WHERE c.table_schema = %s AND c.table_name = %s
            ORDER BY c.ordinal_position
        """, (TARGET_SCHEMA, tname))
        cols = cur.fetchall()
        col_rows = []
        for c in cols:
            dtype = c["udt_name"] if c["data_type"] == "USER-DEFINED" else c["data_type"]
            max_len = f"({c['character_maximum_length']})" if c["character_maximum_length"] else ""
            col_rows.append([
                safe_str(c["ordinal_position"]),
                safe_str(c["column_name"]),
                f"{dtype}{max_len}",
                safe_str(c["is_nullable"]),
                safe_str(c["column_default"]),
            ])
        lines.append(md_table(
            ["#", "Column Name", "Data Type", "Nullable", "Default"],
            col_rows
        ))

        # 4c. Primary keys
        lines.append(f"\n#### Primary Key(s)\n")
        cur.execute("""
            SELECT kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
               AND tc.table_schema    = kcu.table_schema
            WHERE tc.constraint_type = 'PRIMARY KEY'
              AND tc.table_schema    = %s
              AND tc.table_name      = %s
            ORDER BY kcu.ordinal_position
        """, (TARGET_SCHEMA, tname))
        pks = cur.fetchall()
        if pks:
            lines.append(", ".join(f"`{r['column_name']}`" for r in pks) + "\n")
        else:
            lines.append("_No primary key defined._\n")

        # 4d. Indexes
        lines.append(f"\n#### Indexes\n")
        cur.execute("""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE schemaname = %s AND tablename = %s
        """, (TARGET_SCHEMA, tname))
        idxs = cur.fetchall()
        if idxs:
            idx_rows = [[safe_str(i["indexname"]), safe_str(i["indexdef"])] for i in idxs]
            lines.append(md_table(["Index Name", "Definition"], idx_rows))
        else:
            lines.append("_No indexes found._\n")

        # 4e. Foreign Keys
        lines.append(f"\n#### Foreign Keys\n")
        cur.execute("""
            SELECT
                kcu.column_name,
                ccu.table_schema AS foreign_schema,
                ccu.table_name   AS foreign_table,
                ccu.column_name  AS foreign_column
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
               AND tc.table_schema    = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
              AND tc.table_schema    = %s
              AND tc.table_name      = %s
        """, (TARGET_SCHEMA, tname))
        fks = cur.fetchall()
        if fks:
            fk_rows = [[safe_str(f["column_name"]), f"{f['foreign_schema']}.{f['foreign_table']}", safe_str(f["foreign_column"])] for f in fks]
            lines.append(md_table(["Column", "References Table", "References Column"], fk_rows))
        else:
            lines.append("_No foreign keys._\n")

        # 4f. Check Constraints
        lines.append(f"\n#### Check Constraints\n")
        cur.execute("""
            SELECT cc.constraint_name, cc.check_clause
            FROM information_schema.check_constraints cc
            JOIN information_schema.table_constraints tc
                ON cc.constraint_name = tc.constraint_name
            WHERE tc.table_schema = %s AND tc.table_name = %s
        """, (TARGET_SCHEMA, tname))
        checks = cur.fetchall()
        if checks:
            chk_rows = [[safe_str(c["constraint_name"]), safe_str(c["check_clause"])] for c in checks]
            lines.append(md_table(["Constraint Name", "Check Clause"], chk_rows))
        else:
            lines.append("_No check constraints._\n")

        # 4g. Sample data (up to 4 rows)
        lines.append(f"\n#### Sample Data (up to 4 rows)\n")
        if row_count == 0:
            lines.append("_Table is empty — no data yet._\n")
        else:
            col_names = [c["column_name"] for c in cols]
            cur.execute(f"SELECT * FROM {full_table} LIMIT 4")
            data_rows = cur.fetchall()
            sample_rows = [[safe_str(row[cn]) for cn in col_names] for row in data_rows]
            lines.append(md_table(col_names, sample_rows))

        # 4h. Unique values summary for key columns
        lines.append(f"\n#### Unique Value Counts (key columns)\n")
        key_cols = [c["column_name"] for c in cols if c["column_name"] in ("email", "status", "permission_type", "event_type", "application", "is_active")]
        if key_cols and row_count > 0:
            uv_rows = []
            for col in key_cols:
                cur.execute(f"SELECT COUNT(DISTINCT {col}) AS cnt FROM {full_table}")
                uv_rows.append([col, str(cur.fetchone()["cnt"])])
            lines.append(md_table(["Column", "Distinct Values"], uv_rows))
        else:
            lines.append("_Not applicable._\n")

    # ── 5. Overall Summary ─────────────────────────────────
    lines.append("\n---\n\n## 5. Summary\n")
    summary_rows = []
    for tname in table_names:
        cur.execute(f"SELECT COUNT(*) AS cnt FROM {TARGET_SCHEMA}.{tname}")
        cnt = cur.fetchone()["cnt"]
        summary_rows.append([f"`{TARGET_SCHEMA}.{tname}`", str(cnt)])
    lines.append(md_table(["Table", "Row Count"], summary_rows))
    lines.append(f"\n**Exploration completed at:** `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`\n")

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────
# Entry Point
# ─────────────────────────────────────────────────────────

def main():
    print("Connecting to PostgreSQL...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.set_session(readonly=True, autocommit=True)
        print("✅ Connected successfully.")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return

    try:
        print("Running exploration queries...")
        report = explore(conn)
    except Exception as e:
        print(f"❌ Error during exploration: {e}")
        import traceback
        traceback.print_exc()
        return
    finally:
        conn.close()

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"✅ Report written to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
