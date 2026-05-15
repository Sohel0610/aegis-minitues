import requests
import json
import urllib3
import sys

# Suppress SSL warnings for corporate proxy
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration
API_KEY = "tgNuM80eYUxtV0TX!Aa3furfuUcg"
FETCH_URL = "https://www.falconebiz.com/api/director_details"
UPDATE_URL = "https://www.falconebiz.com/api/request_update"
DIN = "11284690"

# Adani Cloud Proxy
PROXIES = {
    "http": "http://cloudproxy.adani.com:8080",
    "https": "http://cloudproxy.adani.com:8080"
}

def test_api():
    print("\n--- Director API Testing Tool ---")
    print(f"Target DIN: {DIN}")
    print("-" * 30)
    print("Select API to test:")
    print("[1] Update API (Request fresh crawl from MCA)")
    print("[2] Fetch API (Get current registry data)")
    
    choice = input("\nEnter choice (1 or 2): ").strip()
    
    if choice == '1':
        url = UPDATE_URL
        print(f"\nCalling Update API: {url}...")
    elif choice == '2':
        url = FETCH_URL
        print(f"\nCalling Fetch API: {url}...")
    else:
        print("Invalid choice. Exiting.")
        return

    headers = {
        "Content-Type": "application/json",
        "Authorization": API_KEY,
        "Din": DIN
    }

    try:
        response = requests.get(
            url, 
            headers=headers, 
            proxies=PROXIES, 
            verify=False, 
            timeout=30
        )
        
        print(f"\nHTTP Status Code: {response.status_code}")
        
        print("\n--- RESPONSE HEADERS ---")
        for key, value in response.headers.items():
            print(f"{key}: {value}")

        print("\n--- RAW RESPONSE BODY ---")
        print(response.text)
        print("\n" + "-" * 30)

    except Exception as e:
        print(f"\nError occurred: {e}")

if __name__ == "__main__":
    test_api()
