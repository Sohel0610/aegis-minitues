import urllib.request
import json
import sys

try:
    resp = urllib.request.urlopen("http://127.0.0.1:8000/openapi.json").read()
    data = json.loads(resp)
    routes = [p for p in data.get("paths", {}).keys()]
    chat_routes = [r for r in routes if "chat" in r]
    print("Detected Chat Routes:")
    for r in chat_routes:
        print(f"- {r}")
except Exception as e:
    print(f"Failed to fetch routes: {e}")
