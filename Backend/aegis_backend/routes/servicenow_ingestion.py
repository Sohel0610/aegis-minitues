import json
import os
import psycopg2
from dotenv import load_dotenv

def clean_pan(pan):
    if not pan:
        return ""
    pan = str(pan).strip().upper()
    if pan == "NULL" or pan == "NONE" or "NO PAN" in pan:
        return ""
    return pan

def clean_qty(qty):
    if not qty:
        return 0
    qty_str = str(qty).strip().lower()
    if qty_str in ["", "null", "none"]:
        return 0
    try:
        return int(float(qty_str))
    except ValueError:
        return 0

def run_ingestion():
    env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
    load_dotenv(env_path)

    db_host = os.getenv('DB_HOST') or '192.168.0.56'
    db_port = os.getenv('DB_PORT') or '5436'
    db_name = os.getenv('DB_NAME') or 'aegis_insider'
    db_user = os.getenv('DB_USER') or 'postgres'
    db_password = os.getenv('DB_PASSWORD') or 'postgres'

    # Resolve JSON path dynamically (check both project root and Backend/ folder)
    _routes_dir = os.path.dirname(os.path.abspath(__file__))
    _backend_dir = os.path.dirname(_routes_dir)
    _project_root = os.path.dirname(_backend_dir)
    _true_root = os.path.dirname(_project_root)

    default_json = os.path.join(_true_root, 'servicenow_data.json')
    backend_json = os.path.join(_project_root, 'servicenow_data.json')
    
    json_path = default_json
    if os.path.exists(backend_json):
        if not os.path.exists(default_json) or os.path.getsize(backend_json) > os.path.getsize(default_json):
            json_path = backend_json

    if not os.path.exists(json_path):
        print(f"ServiceNow JSON file not found at: {json_path}")
        print("Creating empty placeholder — sync will populate it on the next API call.")
        os.makedirs(os.path.dirname(json_path), exist_ok=True)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump({"result": {"result": []}}, f, indent=4)
        return True  # Nothing to ingest yet, but not a failure

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    items = data.get('result', {}).get('result', [])
    if not isinstance(items, list):
        print("Unexpected JSON structure — 'result.result' is not a list.")
        return False
    print(f"Loaded {len(items)} items from ServiceNow JSON.")

    conn = psycopg2.connect(
        host=db_host,
        port=db_port,
        dbname=db_name,
        user=db_user,
        password=db_password
    )
    conn.autocommit = False
    cur = conn.cursor()

    try:
        print("Upserting ServiceNow records into database (safe update — no data loss)...")
        # Ensure unique constraints exist so ON CONFLICT works
        cur.execute("""
            DO $$ BEGIN
                BEGIN
                    ALTER TABLE public.servicenow_declarations ADD CONSTRAINT uq_snd_ritm UNIQUE (ritm_number);
                EXCEPTION WHEN duplicate_table THEN NULL; END;
                BEGIN
                    ALTER TABLE public.servicenow_preclearances ADD CONSTRAINT uq_snp_ritm UNIQUE (ritm_number);
                EXCEPTION WHEN duplicate_table THEN NULL; END;
            END $$;
        """)
        conn.commit()

        # Company Column mapping to Company ID in DB
        # Columns in DB: 1: AESL, 2: AEL, 3: AGEL, 4: APSEZL, 5: Ambuja (ACL), 6: Sanghi
        company_mapping = {
            'AESL Qty': 1, 'AESL qty': 1,
            'AEL Qty': 2, 'AEL qty': 2,
            'AGEL Qty': 3, 'AGEL qty': 3,
            'APSEZL Qty': 4, 'APSEZL qty': 4,
            'ACL Qty': 5, 'ACL qty': 5,
            'Sanghi Qty': 6, 'Sanghi qty': 6
        }

        declaration_count = 0
        declaration_new = 0
        declaration_updated = 0
        holdings_count = 0
        preclearance_count = 0
        preclearance_new = 0
        preclearance_updated = 0
        preclearance_details_count = 0

        # Snapshot existing states for change detection
        cur.execute("SELECT ritm_number, state FROM public.servicenow_declarations")
        existing_decl_states = {r[0]: r[1] for r in cur.fetchall()}
        cur.execute("SELECT ritm_number, state FROM public.servicenow_preclearances")
        existing_pc_states = {r[0]: r[1] for r in cur.fetchall()}
        changes_found = False

        for item in items:
            ritm = item.get('number')
            email = item.get('email')
            requested_for = item.get('requested_for')
            state = item.get('state')
            catalog_item = item.get('catalog_item')
            variables = item.get('variables', {})

            if not ritm or not email:
                continue

            email_clean = email.strip().lower()

            if catalog_item == 'Self-Declaration of Shares':
                employee_code = variables.get('Employee Code')
                designation = variables.get('Designation')
                declaration_date = variables.get('Date of Self-Declaration')
                phase = variables.get('Self Declaration Phase')
                fiscal_year = variables.get('Fiscal Year')

                # Change detection before upsert
                if ritm in existing_decl_states:
                    old_state = existing_decl_states[ritm]
                    if old_state != state:
                        print(f"  [UPDATED] {ritm} ({requested_for}) — state changed: '{old_state}' → '{state}'")
                        changes_found = True
                    declaration_updated += 1
                else:
                    print(f"  [NEW]     {ritm} ({requested_for}) — Self-Declaration added")
                    changes_found = True
                    declaration_new += 1

                # Insert or update Declaration Master (upsert by ritm_number)
                cur.execute("""
                    INSERT INTO public.servicenow_declarations 
                    (ritm_number, requested_for, email, employee_code, designation, declaration_date, phase, fiscal_year, state)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (ritm_number) DO UPDATE SET
                        requested_for = EXCLUDED.requested_for,
                        email = EXCLUDED.email,
                        employee_code = EXCLUDED.employee_code,
                        designation = EXCLUDED.designation,
                        declaration_date = EXCLUDED.declaration_date,
                        phase = EXCLUDED.phase,
                        fiscal_year = EXCLUDED.fiscal_year,
                        state = EXCLUDED.state
                """, (ritm, requested_for, email_clean, employee_code, designation, declaration_date or None, phase, fiscal_year, state))
                declaration_count += 1

                # Delete existing holdings for this RITM then re-insert (child rows keyed by RITM)
                cur.execute("DELETE FROM public.servicenow_holdings WHERE ritm_number = %s", (ritm,))
                mrvs_details = item.get('mrvs', {}).get('Details', [])
                for h in mrvs_details:
                    name = h.get('Name')
                    relationship = h.get('Relationship', 'self')
                    pan = clean_pan(h.get('PAN Card'))

                    if not name:
                        continue

                    # Check holdings across mapped companies
                    for col, company_id in company_mapping.items():
                        qty_val = h.get(col)
                        qty = clean_qty(qty_val)
                        
                        # Only store holdings greater than 0
                        if qty > 0:
                            cur.execute("""
                                INSERT INTO public.servicenow_holdings 
                                (ritm_number, name, relationship, pan_card, company_id, declared_quantity)
                                VALUES (%s, %s, %s, %s, %s, %s)
                            """, (ritm, name, relationship, pan, company_id, qty))
                            holdings_count += 1

            elif catalog_item == 'Application to Buy/Sell Shares':
                employee_code = variables.get('Employee Code')
                designation = variables.get('Designation')
                phase = variables.get('Self Declaration Phase')
                fiscal_year = variables.get('Fiscal Year')

                # Change detection before upsert
                if ritm in existing_pc_states:
                    old_state = existing_pc_states[ritm]
                    if old_state != state:
                        print(f"  [UPDATED] {ritm} ({requested_for}) — state changed: '{old_state}' → '{state}'")
                        changes_found = True
                    preclearance_updated += 1
                else:
                    print(f"  [NEW]     {ritm} ({requested_for}) — Pre-clearance added")
                    changes_found = True
                    preclearance_new += 1

                # Insert or update Pre-Clearance Master (upsert by ritm_number)
                cur.execute("""
                    INSERT INTO public.servicenow_preclearances 
                    (ritm_number, requested_for, email, employee_code, designation, phase, fiscal_year, state)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (ritm_number) DO UPDATE SET
                        requested_for = EXCLUDED.requested_for,
                        email = EXCLUDED.email,
                        employee_code = EXCLUDED.employee_code,
                        designation = EXCLUDED.designation,
                        phase = EXCLUDED.phase,
                        fiscal_year = EXCLUDED.fiscal_year,
                        state = EXCLUDED.state
                """, (ritm, requested_for, email_clean, employee_code, designation, phase, fiscal_year, state))
                preclearance_count += 1

                # Delete existing detail rows for this RITM then re-insert
                cur.execute("DELETE FROM public.servicenow_preclearance_details WHERE ritm_number = %s", (ritm,))

                # Parse Pre-Clearance Details MRVS
                mrvs_details = item.get('mrvs', {}).get('Self-Declared Share Details', [])
                for pc_detail in mrvs_details:
                    name = pc_detail.get('Name')
                    relationship = pc_detail.get('Relationship', 'self')
                    pan = clean_pan(pc_detail.get('PAN Card'))
                    qty = clean_qty(pc_detail.get('Quantity'))

                    if not name:
                        continue

                    # Insert detail record
                    cur.execute("""
                        INSERT INTO public.servicenow_preclearance_details 
                        (ritm_number, name, relationship, pan_card, approved_quantity)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (ritm, name, relationship, pan, qty))
                    preclearance_details_count += 1

        conn.commit()
        print("")
        print("=== ServiceNow Ingestion Complete ===")
        print(f"  Declarations : {declaration_count} total  ({declaration_new} new, {declaration_updated} updated)")
        print(f"  Holdings     : {holdings_count} records")
        print(f"  Pre-clearances: {preclearance_count} total ({preclearance_new} new, {preclearance_updated} updated)")
        print(f"  PC Details   : {preclearance_details_count} records")
        if not changes_found:
            print("  >> No changes detected — all records match the previous sync.")
        else:
            print(f"  >> Changes detected: {declaration_new + preclearance_new} new record(s), state changes logged above.")
        print("======================================")
        conn.close()
        return True
    except Exception as e:
        conn.rollback()
        conn.close()
        print(f"Error during ingestion execution: {e}")
        return False

if __name__ == "__main__":
    run_ingestion()
