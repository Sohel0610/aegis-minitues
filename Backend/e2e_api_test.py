import requests
import time
import sys

base_url = "http://127.0.0.1:8000"

endpoints = [
    ("/api/health", "GET"),
    ("/api/directors", "GET"),
    ("/api/directors-for-minutes", "GET"),
    ("/api/company-count", "GET"),
    ("/api/directors-disclosures/analytics", "GET"),
    ("/api/cross-directorship", "GET"),
    ("/api/clustering", "GET"),
    ("/api/network", "GET"),
    ("/api/wtd-count", "GET"),
    ("/api/companies-with-director-count", "GET"),
    ("/api/bse-alerts", "GET"),
    ("/api/sebi-analysis-data?page=1&limit=2", "GET"),
    ("/", "GET"), # Test index.html fallback
]

print(f"Starting E2E Backend Tests against {base_url}\n")

failed = 0
for endpoint, method in endpoints:
    url = f"{base_url}{endpoint}"
    print(f"Testing {method} {endpoint}...")
    try:
        start = time.time()
        if method == "GET":
            resp = requests.get(url, timeout=5)
        else:
            resp = requests.post(url, timeout=5)
        latency = time.time() - start
        
        status = "PASSED" if resp.status_code == 200 else "WARNING/FAILED"
        if resp.status_code != 200:
            failed += 1
            
        print(f"  Status code: {resp.status_code}")
        print(f"  Latency: {latency:.2f}s")
        if resp.status_code == 200:
            ctype = resp.headers.get("Content-Type", "")
            if "application/json" in ctype:
                preview = str(resp.json())[:100]
                print(f"  Body (JSON preview): {preview}...")
            elif "text/html" in ctype:
                preview = resp.text.split('\n')[0][:100]
                print(f"  Body (HTML preview): {preview}...")
            else:
                print(f"  Body preview: {resp.text[:100]}...")
        else:
            print(f"  Error Body: {resp.text[:100]}")
            
    except requests.exceptions.RequestException as e:
        print(f"  ERROR: Request failed: {e}")
        failed += 1
    print("-" * 40)

if failed == 0:
    print("SUCCESS: All tests passed!")
    sys.exit(0)
else:
    print(f"FAILURE: {failed} tests failed.")
    sys.exit(1)
