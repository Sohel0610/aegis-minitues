import os
import sys
import json
import time
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

# Set up paths
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_BACKEND_DIR = os.path.dirname(_SCRIPT_DIR)  # Backend/aegis_backend
_PROJECT_ROOT = os.path.dirname(_BACKEND_DIR)  # project root

# Load environment variables
env_path = os.path.join(_BACKEND_DIR, ".env")
load_dotenv(env_path)

API_URL = os.getenv("SERVICENOW_API_URL")
USERNAME = os.getenv("SERVICENOW_USERNAME")
PASSWORD = os.getenv("SERVICENOW_PASSWORD")

def parse_description_to_mrvs(description, catalog_item, requested_for):
    """
    Parses the comma-separated or newline-separated description string
    into standard variables and MRVS structures.
    """
    variables = {}
    mrvs = {}
    
    if not description:
        return variables, mrvs

    # Clean description into key-value pairs
    lines = []
    for part in description.split('\n'):
        part = part.strip()
        if not part:
            continue
        # Split by comma-space if they are on the same line
        for subpart in part.split(',  '):
            subpart = subpart.strip()
            if ':' in subpart:
                lines.append(subpart)
            else:
                # Try single comma split
                for chunk in subpart.split(','):
                    chunk = chunk.strip()
                    if ':' in chunk:
                        lines.append(chunk)

    parsed_fields = {}
    for line in lines:
        if ':' in line:
            parts = line.split(':', 1)
            k = parts[0].strip()
            v = parts[1].strip()
            # De-duplicate or set value
            if k not in parsed_fields or not parsed_fields[k]:
                parsed_fields[k] = v

    # Populate top-level variables used by ingestion
    variables['Employee Code'] = parsed_fields.get('Employee Code') or parsed_fields.get('employee_code')
    variables['Designation'] = parsed_fields.get('Designation') or parsed_fields.get('designation')
    variables['Date of Self-Declaration'] = parsed_fields.get('Date of Self-Declaration') or parsed_fields.get('date_of_self_declaration')
    variables['Self Declaration Phase'] = parsed_fields.get('Self Declaration Phase') or parsed_fields.get('u_phase')
    variables['Fiscal Year'] = parsed_fields.get('Fiscal Year') or parsed_fields.get('u_fiscal_year')

    # Reconstruct MRVS holdings/quantities
    if catalog_item == 'Application to Buy/Sell Shares':
        name = parsed_fields.get('Name') or parsed_fields.get('u_name') or requested_for
        rel = parsed_fields.get('Relationship') or parsed_fields.get('u_relationship') or parsed_fields.get('relation') or 'self'
        pan = parsed_fields.get('PAN Card') or parsed_fields.get('u_pan_card') or parsed_fields.get('pan_card') or ''
        qty = parsed_fields.get('Share Quantity') or parsed_fields.get('share_quantity') or parsed_fields.get('Quantity') or parsed_fields.get('quantity') or '0'
        
        mrvs['Self-Declared Share Details'] = [{
            'Name': name,
            'Relationship': rel,
            'PAN Card': pan,
            'Quantity': qty
        }]
    
    elif catalog_item == 'Self-Declaration of Shares':
        name = parsed_fields.get('Name') or parsed_fields.get('u_name') or requested_for
        rel = parsed_fields.get('Relationship') or parsed_fields.get('u_relationship') or parsed_fields.get('relation') or 'self'
        pan = parsed_fields.get('PAN Card') or parsed_fields.get('u_pan_card') or parsed_fields.get('pan_card') or ''
        
        # Pull company quantities if present
        ael_qty = parsed_fields.get('AEL Qty') or parsed_fields.get('ael_qty') or '0'
        aesl_qty = parsed_fields.get('AESL Qty') or parsed_fields.get('aesl_qty') or '0'
        agel_qty = parsed_fields.get('AGEL Qty') or parsed_fields.get('agel_qty') or '0'
        apsezl_qty = parsed_fields.get('APSEZL Qty') or parsed_fields.get('apsezl_qty') or '0'
        acl_qty = parsed_fields.get('ACL Qty') or parsed_fields.get('acl_qty') or '0'
        sanghi_qty = parsed_fields.get('Sanghi Qty') or parsed_fields.get('sanghi_qty') or '0'
        
        mrvs['Details'] = [{
            'Name': name,
            'Relationship': rel,
            'PAN Card': pan,
            'AESL Qty': aesl_qty,
            'AEL Qty': ael_qty,
            'AGEL Qty': agel_qty,
            'APSEZL Qty': apsezl_qty,
            'ACL Qty': acl_qty,
            'Sanghi Qty': sanghi_qty
        }]
        
    return variables, mrvs

def fetch_all():
    if not API_URL or not USERNAME or not PASSWORD:
        print("[ERROR] Credentials missing from .env file.")
        sys.exit(1)
        
    domain = API_URL.split("/api/")[0]
    table_url = f"{domain}/api/now/table/sc_req_item"
    
    print("=" * 70)
    print("     AEGIS - ServiceNow Bulk Historical Data Downloader")
    print("=" * 70)
    print(f"Connecting to: {domain}")
    
    # 1. Get total record count first
    count_params = {
        "sysparm_query": "cat_item.name=Self-Declaration of Shares^ORcat_item.name=Application to Buy/Sell Shares",
        "sysparm_fields": "sys_id"
    }
    
    try:
        print("Calculating total matching records in ServiceNow...")
        resp = requests.get(
            table_url,
            auth=HTTPBasicAuth(USERNAME, PASSWORD),
            headers={"Accept": "application/json", "X-Want-Display-Value": "true"},
            params={**count_params, "sysparm_limit": "1"},
            timeout=25,
            verify=False
        )
        if resp.status_code != 200:
            print(f"[ERROR] API failed with status {resp.status_code}: {resp.text}")
            sys.exit(1)
            
        total_records = int(resp.headers.get("X-Total-Count", 114657))
        print(f"[OK] Total records to fetch: {total_records}")
    except Exception as e:
        print(f"[WARNING] Failed to fetch exact total, using default 115,000. Error: {e}")
        total_records = 115000

    # 2. Paginated Fetch Loop
    limit = 5000
    offset = 0
    all_items = []
    
    start_time = time.time()
    
    while offset < total_records:
        print(f"Fetching chunk: offset={offset}, limit={limit} ({(offset/total_records)*100:.1f}% complete)...")
        
        params = {
            "sysparm_query": "cat_item.name=Self-Declaration of Shares^ORcat_item.name=Application to Buy/Sell Shares",
            "sysparm_fields": "sys_id,number,state,description,cat_item.name,request.requested_for.name,request.requested_for.email,sys_created_on",
            "sysparm_limit": str(limit),
            "sysparm_offset": str(offset)
        }
        
        retries = 3
        success = False
        while retries > 0 and not success:
            try:
                resp = requests.get(
                    table_url,
                    auth=HTTPBasicAuth(USERNAME, PASSWORD),
                    headers={"Accept": "application/json", "X-Want-Display-Value": "true"},
                    params=params,
                    timeout=45,
                    verify=False
                )
                if resp.status_code == 200:
                    success = True
                else:
                    print(f"  [RETRY] Server returned {resp.status_code}, retrying...")
                    retries -= 1
                    time.sleep(2)
            except Exception as err:
                print(f"  [RETRY] Error occurred: {err}, retrying...")
                retries -= 1
                time.sleep(3)
                
        if not success:
            print(f"[ERROR] Failed to fetch chunk at offset {offset} after multiple retries. Aborting.")
            sys.exit(1)
            
        chunk_data = resp.json().get("result", [])
        if not chunk_data:
            print("  No more records returned from API.")
            break
            
        # Parse and format each record
        for raw_item in chunk_data:
            ritm = raw_item.get("number")
            desc = raw_item.get("description") or ""
            cat_item = raw_item.get("cat_item.name")
            req_for = raw_item.get("request.requested_for.name")
            email = raw_item.get("request.requested_for.email")
            state = raw_item.get("state")
            created_on = raw_item.get("sys_created_on")
            
            # Parse variables and holdings from the description block
            variables, mrvs = parse_description_to_mrvs(desc, cat_item, req_for)
            
            # Reconstruct the standard JSON schema expected by the ingestion engine
            formatted_item = {
                "sys_id": raw_item.get("sys_id"),
                "number": ritm,
                "state": state,
                "email": email,
                "requested_for": req_for,
                "catalog_item": cat_item,
                "created_on": created_on,
                "variables": variables,
                "mrvs": mrvs
            }
            all_items.append(formatted_item)
            
        offset += limit
        
    # 3. Save to file
    output_path = os.path.join(_PROJECT_ROOT, "servicenow_data.json")
    print(f"\nSaving {len(all_items)} records to {output_path}...")
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({"result": {"result": all_items}}, f, indent=4, ensure_ascii=False)
        
    elapsed = time.time() - start_time
    print("=" * 70)
    print("  [DONE] DOWNLOAD AND RECONCILIATION COMPLETE!")
    print(f"  Total records fetched and structured: {len(all_items)}")
    print(f"  Time elapsed: {elapsed/60:.2f} minutes")
    print(f"  File saved at: {output_path}")
    print("=" * 70)

if __name__ == "__main__":
    fetch_all()
