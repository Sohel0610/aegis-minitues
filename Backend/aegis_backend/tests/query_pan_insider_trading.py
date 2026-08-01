import sqlite3
import argparse
import json
import os
import sys
import urllib.parse
import urllib.request

def query_tables(db_path, pan):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    results = []
    for table in ["Added", "Removed", "Changed", "All_Data"]:
        if table not in tables:
            continue
        cols = [r[1] for r in cur.execute(f"PRAGMA table_info({table})").fetchall()]
        pang_col = "PANGIR1" if "PANGIR1" in cols else ("PANGIR" if "PANGIR" in cols else None)
        if not pang_col:
            continue
        cur.execute(f"SELECT * FROM {table} WHERE {pang_col} = ?", (pan,))
        rows = cur.fetchall()
        for row in rows:
            data = dict(zip(cols, row))
            results.append({
                "table": table,
                "pangir": data.get("PANGIR1") or data.get("PANGIR"),
                "NAME1_latest": data.get("NAME1_latest"),
                "EMAIL1_latest": data.get("EMAIL1_latest"),
                "NAME1_older": data.get("NAME1_older"),
                "EMAIL1_older": data.get("EMAIL1_older"),
                "POSITION_latest": data.get("POSITION_latest"),
                "POSITION_older": data.get("POSITION_older"),
                "POSITION_DIFFERENCE": data.get("POSITION_DIFFERENCE"),
                "STATUS": data.get("STATUS")
            })
    conn.close()
    return results

def call_api(company, depository, pan):
    url = "http://localhost:8000/api/insider-trading/enhanced-details" + "?" + urllib.parse.urlencode({
        "company": company,
        "depository": depository
    })
    try:
        with urllib.request.urlopen(url) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"error": str(e)}
    matches = []
    for key in ["top_new_investors", "top_exits", "top_buyers", "top_sellers"]:
        items = data.get(key, [])
        for itm in items:
            val = (itm.get("pangir") or "").strip().upper()
            if val == pan.strip().upper():
                matches.append({
                    "list": key,
                    "pangir": itm.get("pangir"),
                    "name": itm.get("name"),
                    "email": itm.get("email"),
                    "position_latest": itm.get("position_latest"),
                    "position_older": itm.get("position_older"),
                    "position_difference": itm.get("position_difference")
                })
    return {"matches": matches}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=os.path.join(os.path.dirname(__file__), "..", "public", "AdaniInsiderTraders", "user_Adanitrans_20251203_155023", "BENPOS-CDSL_analysis_results.db"))
    parser.add_argument("--pan", default="AAACD5556D")
    args = parser.parse_args()
    db_path = os.path.abspath(args.db)
    pan = args.pan
    db_results = query_tables(db_path, pan)
    print(json.dumps({"db_path": db_path, "pan": pan, "db_results": db_results}, ensure_ascii=False))
    api_results = call_api("Adanitrans", "CDSL", pan)
    print(json.dumps({"api_results": api_results}, ensure_ascii=False))

if __name__ == "__main__":
    main()

