import os
import json
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_URL = os.getenv("SERVICENOW_API_URL")
USERNAME = os.getenv("SERVICENOW_USERNAME")
PASSWORD = os.getenv("SERVICENOW_PASSWORD")

def fetch_ritms_yesterday(verify_cert=True, timeout=30):
    if not API_URL or not USERNAME or not PASSWORD:
        print("Error: ServiceNow credentials not found in environment variables.")
        return {
            "status": 0,
            "has_data": False,
            "message": "Missing credentials",
            "result": []
        }

    url = API_URL
    if not (url.startswith("http://") or url.startswith("https://")):
        url = "https://" + url

    resp = requests.get(
        url,
        auth=HTTPBasicAuth(USERNAME, PASSWORD),
        headers={
            "Accept": "application/json"
        },
        timeout=timeout,
        verify=verify_cert
    )

    print("resp : ", resp)
    print("resp headers: ", resp.headers)
    print("resp text: ", resp.text)

    # Handle "No Content"
    if resp.status_code == 204:
        return {
            "status": 204,
            "has_data": False,
            "message": "No content returned by the API for 'yesterday'.",
            "result": []
        }

    # Raise for other HTTP errors
    resp.raise_for_status()

    # If Content-Type says JSON, try parse; otherwise return raw text
    ctype = (resp.headers.get("Content-Type") or "").lower()
    if "application/json" in ctype:
        # Could still be empty body; guard it
        if not resp.text.strip():
            return {
                "status": resp.status_code,
                "has_data": False,
                "message": "Empty JSON body.",
                "result": []
            }
        return {
            "status": resp.status_code,
            "has_data": True,
            "result": resp.json()
        }
    else:
        # Fallback for non-JSON (shouldn't happen here, but safe)
        return {
            "status": resp.status_code,
            "has_data": bool(resp.text.strip()),
            "raw": resp.text
        }

if __name__ == "__main__":
    data = fetch_ritms_yesterday(verify_cert=True)
    print("data : ", data)
    
    # Store data in a file for now
    try:
        with open("servicenow_data.json", "w") as f:
            json.dump(data, f, indent=4)
        print("Data stored in servicenow_data.json")
    except Exception as e:
        print(f"Error saving data: {e}")
