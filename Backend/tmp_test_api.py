import requests
import time

urls = [
    "http://127.0.0.1:8000/api/health",
    "http://127.0.0.1:8000/api/directors",
    "http://127.0.0.1:8000/api/company-count",
    "http://127.0.0.1:8000/api/directors-disclosures/analytics"
]

for url in urls:
    print(f"Testing {url}...")
    try:
        start = time.time()
        # Short timeout to avoid blocking my turn if the server is really dead
        resp = requests.get(url, timeout=5) 
        end = time.time()
        print(f"Status: {resp.status_code}")
        print(f"Latency: {end - start:.2f}s")
        if resp.status_code == 200:
            print(f"Body: {resp.text[:100]}...")
        else:
            print(f"Error: {resp.text}")
    except Exception as e:
        print(f"FAILED after 5s: {type(e).__name__}")
    print("-" * 20)
