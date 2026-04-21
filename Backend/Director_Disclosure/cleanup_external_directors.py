"""
cleanup_external_directors.py
─────────────────────────────────────────────────────────────────────────────
One-time cleanup script implementing the Two-Layer Registry (Option 2).

WHAT IT DOES:
  1. Creates the external_board_members table if not already done
  2. Moves all directors that were inserted ONLY by the company API sync
     (not from MBP-1 uploads or DIN sync) into external_board_members
  3. Deletes them from directors_master.directors to restore clean Adani roster

HOW IT IDENTIFIES "external" directors:
  A director in directors_master.directors is considered EXTERNAL if:
  - They do NOT appear in directors_data.directors (MBP-1 parsed)
  - AND they have no last_api_sync (never had DIN enriched from Falconebiz DIN API)
  - AND they have no document_summaries record (no MBP-1 uploads)

RUN ONCE. Safe to re-run — uses ON CONFLICT DO NOTHING.
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "aegis_backend", ".env")
if not os.path.exists(env_path):
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(env_path)

def get_conn():
    return psycopg2.connect(
        host=os.getenv('POSTGRES_HOST'),
        port=os.getenv('POSTGRES_PORT', '5432'),
        user=os.getenv('POSTGRES_USER'),
        password=os.getenv('POSTGRES_PASSWORD'),
        dbname=os.getenv('POSTGRES_DATABASE_DIRECTOR', 'director_disclosure_system'),
        sslmode='require'
    )

def run_cleanup():
    print("═══════════════════════════════════════════════════════════════")
    print("  AEGIS TWO-LAYER REGISTRY CLEANUP")
    print("  Separating group directors from externally-added entries")
    print("═══════════════════════════════════════════════════════════════\n")

    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # ── Step 1: Ensure external_board_members table exists ────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS directors_master.external_board_members (
            id SERIAL PRIMARY KEY,
            din TEXT NOT NULL,
            name TEXT,
            cin TEXT NOT NULL,
            company_name TEXT,
            designation TEXT,
            appointment_date TEXT,
            source TEXT DEFAULT 'COMPANY_API',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(din, cin)
        )
    """)
    conn.commit()
    print("  [✓] external_board_members table ready.\n")

    # ── Step 2: Identify external directors ───────────────────────────
    # External = in directors_master.directors BUT:
    # - NOT in directors_data.directors (MBP-1 sourced)
    # - AND no last_api_sync (never enriched via DIN API)
    # - AND no document_summaries (no MBP-1 file)
    cur.execute("""
        SELECT d.id, d.din, d.name
        FROM directors_master.directors d
        WHERE
            -- Not from MBP-1 documents
            NOT EXISTS (
                SELECT 1 FROM directors_data.directors dd WHERE dd.din = d.din
            )
            -- Not enriched via DIN API
            AND (d.last_api_sync IS NULL)
            -- No MBP-1 file uploaded
            AND NOT EXISTS (
                SELECT 1 FROM directors_data.document_summaries ds
                WHERE TRIM(UPPER(ds.director_name)) = TRIM(UPPER(d.name))
                   OR ds.din = d.din
            )
    """)
    external_dirs = cur.fetchall()
    print(f"  [SCAN] Found {len(external_dirs)} external directors to migrate.\n")

    if not external_dirs:
        print("  [✓] No external directors found. Registry is already clean!")
        conn.close()
        return

    # ── Step 3: Move them to external_board_members ───────────────────
    migrated = 0
    skipped  = 0
    for d in external_dirs:
        din  = d['din']
        name = d['name']

        # Get all their associations for the new table
        cur.execute("""
            SELECT cin, company_name, designation, appointment_date
            FROM directors_master.external_associations
            WHERE din = %s
        """, (din,))
        assocs = cur.fetchall()

        if assocs:
            for a in assocs:
                cur.execute("""
                    INSERT INTO directors_master.external_board_members
                        (din, name, cin, company_name, designation, appointment_date)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (din, cin) DO NOTHING
                """, (din, name, a['cin'], a['company_name'], a['designation'], a['appointment_date']))
        else:
            # No associations but still in master — insert minimal record
            cur.execute("""
                INSERT INTO directors_master.external_board_members (din, name, cin, company_name)
                VALUES (%s, %s, 'UNKNOWN', 'No company record')
                ON CONFLICT (din, cin) DO NOTHING
            """, (din, name))

        migrated += 1
        print(f"  [MIGRATE] {name} (DIN: {din}) → external_board_members ({len(assocs)} associations)")

    conn.commit()
    print(f"\n  [✓] Migrated {migrated} external directors to external_board_members.")

    # ── Step 4: Remove from directors_master.directors ────────────────
    external_ids = [d['id'] for d in external_dirs]
    cur.execute("""
        DELETE FROM directors_master.directors
        WHERE id = ANY(%s)
    """, (external_ids,))
    deleted = cur.rowcount
    conn.commit()
    print(f"  [✓] Removed {deleted} entries from directors_master.directors.\n")

    # ── Step 5: Also clean their orphan associations ───────────────────
    external_dins = [d['din'] for d in external_dirs]
    cur.execute("""
        DELETE FROM directors_master.external_associations
        WHERE din = ANY(%s)
    """, (external_dins,))
    cleaned = cur.rowcount
    conn.commit()
    print(f"  [✓] Cleaned {cleaned} orphan records from external_associations.\n")

    # ── Final count ───────────────────────────────────────────────────
    cur.execute("SELECT COUNT(*) AS cnt FROM directors_master.directors")
    group_count = cur.fetchone()['cnt']
    cur.execute("SELECT COUNT(*) AS cnt FROM directors_master.external_board_members")
    ext_count = cur.fetchone()['cnt']

    conn.close()
    print("═══════════════════════════════════════════════════════════════")
    print(f"  CLEANUP COMPLETE")
    print(f"  Group Directors (Adani roster) : {group_count}")
    print(f"  External Board Members catalogued : {ext_count}")
    print("═══════════════════════════════════════════════════════════════")

if __name__ == "__main__":
    run_cleanup()
