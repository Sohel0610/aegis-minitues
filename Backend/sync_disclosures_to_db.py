import os
import sqlite3
import re

def sync_disclosures():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    disclosures_dir = os.path.join(base_dir, "Backend", "Director_Disclosure", "Output_Disclosures", "2024-25")
    db_path = os.path.join(base_dir, "Backend", "aegis_backend", "public", "local_fallback.db")

    if not os.path.exists(disclosures_dir):
        print(f"[ERR] Disclosures directory not found: {disclosures_dir}")
        return

    print(f"Opening database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create external_board_members table if missing
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS external_board_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            din TEXT NOT NULL,
            name TEXT,
            cin TEXT NOT NULL DEFAULT '',
            company_name TEXT,
            designation TEXT DEFAULT 'Director',
            appointment_date TEXT,
            status TEXT DEFAULT 'Active',
            source TEXT DEFAULT 'DISCLOSURE_DOCS',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(din, company_name)
        )
    """)

    company_folders = [d for d in os.listdir(disclosures_dir) if os.path.isdir(os.path.join(disclosures_dir, d))]
    print(f"Found {len(company_folders)} company disclosure folders.")

    inserted = 0
    skipped = 0

    for folder in company_folders:
        clean_company_name = folder.replace('_', ' ').strip()
        folder_path = os.path.join(disclosures_dir, folder)
        
        # Check subfolders MBP-1 and DIR-8
        for sub in ['MBP-1', 'DIR-8']:
            sub_path = os.path.join(folder_path, sub)
            if not os.path.exists(sub_path):
                continue

            for fname in os.listdir(sub_path):
                if fname.endswith('.docx') and not fname.startswith('~'):
                    # Filename format: MBP1_FIRST_MIDDLE_LAST_DIN.docx or DIR8_FIRST_MIDDLE_LAST_DIN.docx
                    match = re.search(r'^(?:MBP1|DIR8)_(.+)__?(\d{8})\.docx$', fname, re.IGNORECASE)
                    if not match:
                        match = re.search(r'^(?:MBP1|DIR8)_(.+)_(\d{8})\.docx$', fname, re.IGNORECASE)
                    
                    if match:
                        raw_name = match.group(1).replace('_', ' ').strip()
                        # Format name to Title Case nicely
                        name_parts = [p.capitalize() for p in raw_name.split() if p]
                        formatted_name = " ".join(name_parts)
                        din = match.group(2).strip()

                        try:
                            cursor.execute("""
                                INSERT INTO external_board_members (din, name, cin, company_name, designation, status, source)
                                VALUES (?, ?, '', ?, 'Director', 'Active', 'DISCLOSURE_DOCS')
                                ON CONFLICT(din, company_name) DO UPDATE SET
                                    name=EXCLUDED.name,
                                    status='Active'
                            """, (din, formatted_name, clean_company_name))
                            inserted += 1
                        except Exception as err:
                            skipped += 1

    conn.commit()

    cursor.execute("SELECT COUNT(*) FROM external_board_members")
    total_in_db = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(DISTINCT company_name) FROM external_board_members")
    companies_with_dirs = cursor.fetchone()[0]

    print("\n=== DISCLOSURE SYNC COMPLETE ===")
    print(f"Total Director Relationships in DB: {total_in_db}")
    print(f"Total Unique Companies with Directors: {companies_with_dirs}")
    print(f"New entries inserted/updated: {inserted}")
    conn.close()

if __name__ == "__main__":
    sync_disclosures()
