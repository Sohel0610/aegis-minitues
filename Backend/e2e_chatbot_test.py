import requests
import time
import sys
import json

base_url = "http://127.0.0.1:8000"

endpoints = [
    ("/api/health", "GET", None),
    ("/api/directors", "GET", None),
    ("/api/company-count", "GET", None),
    ("/api/directors-disclosures/analytics", "GET", None),
    ("/api/bse-alerts", "GET", None),
    ("/api/sebi-analysis-data?page=1&limit=2", "GET", None),
    ("/api/chat/message", "POST", {"message": "Tell me about SEBI notifications", "database": "sebi"}),
    ("/api/minutes-chatbot/query", "POST", {"query": "Summarize the meeting", "session_id": "test_session_1"}),
    ("/api/minutes-chatbot/documents", "GET", None),
]

print(f"Starting E2E Backend Tests (Including Chatbots) against {base_url}\n")

failed = 0
for endpoint, method, payload in endpoints:
    url = f"{base_url}{endpoint}"
    print(f"Testing {method} {endpoint}...")
    try:
        start = time.time()
        if method == "GET":
            resp = requests.get(url, timeout=30)
        else:
            resp = requests.post(url, json=payload, timeout=60)
        latency = time.time() - start
        
        status = "PASSED" if resp.status_code == 200 else "WARNING/FAILED"
        if resp.status_code != 200:
            failed += 1
            
        print(f"  Status code: {resp.status_code} ({status})")
        print(f"  Latency: {latency:.2f}s")
        if resp.status_code == 200:
            ctype = resp.headers.get("Content-Type", "")
            if "application/json" in ctype:
                preview = str(resp.json())[:150]
                print(f"  Body (JSON preview): {preview}...")
            else:
                print(f"  Body preview: {resp.text[:150]}...")
        else:
            print(f"  Error Body: {resp.text[:150]}")
            
    except requests.exceptions.Timeout:
        print(f"  ERROR: Request timed out.")
        failed += 1
    except requests.exceptions.RequestException as e:
        print(f"  ERROR: Request failed: {e}")
        failed += 1
    print("-" * 50)

if failed == 0:
    print("SUCCESS: All tests passed! Backend and Chatbots are fully functional.")
    sys.exit(0)
else:
    print(f"FAILURE: {failed} tests failed.")
    sys.exit(1)
