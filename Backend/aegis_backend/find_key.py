import requests

endpoints = [
    "https://login.microsoftonline.com/common/discovery/v2.0/keys",
    "https://login.microsoftonline.com/organizations/discovery/v2.0/keys",
    "https://login.microsoftonline.com/consumers/discovery/v2.0/keys",
    "https://login.microsoftonline.com/04c72f56-1848-46a2-8167-8e5d36510cbc/discovery/v2.0/keys",
    "https://login.windows.net/common/discovery/keys"
]

target_kid = "Nm8hkfCMz6FaGvFOuczCVRmtVe8"

for url in endpoints:
    try:
        resp = requests.get(url)
        keys = resp.json().get('keys', [])
        kids = [k.get('kid') for k in keys]
        if target_kid in kids:
            print(f"FOUND in {url}")
        else:
            print(f"NOT FOUND in {url}. Available: {kids[:2]}...")
    except Exception as e:
        print(f"ERROR reaching {url}: {e}")
