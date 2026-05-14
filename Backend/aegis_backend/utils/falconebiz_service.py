import os
import requests
import urllib3
from dotenv import load_dotenv

# Suppress SSL warnings for corporate proxy
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Load ENV
load_dotenv()

API_KEY = "tgNuM80eYUxtV0TX!Aa3furfuUcg"
UPDATE_URL = "https://www.falconebiz.com/api/request_update"
PROXY = "http://cloudproxy.adani.com:8080"
PROXIES = {"http": PROXY, "https": PROXY}

def trigger_mca_refresh(din=None, cin=None):
    """
    Triggers a live refresh on Falconebiz/MCA side for a specific DIN or CIN.
    Returns: (success_bool, message)
    """
    if not din and not cin:
        return False, "Neither DIN nor CIN provided."

    headers = {
        "Content-Type": "application/json",
        "Authorization": API_KEY
    }
    
    if din:
        headers["Din"] = str(din)
    elif cin:
        headers["Company"] = str(cin)

    try:
        response = requests.post(
            UPDATE_URL, 
            headers=headers, 
            proxies=PROXIES, 
            verify=False, 
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            # Falconebiz usually returns a success message or status
            return True, data.get("message") or "Refresh request triggered successfully. Data will update in 2-5 minutes."
        else:
            return False, f"API Error: {response.status_code} - {response.text}"
            
    except Exception as e:
        return False, f"Exception during refresh request: {str(e)}"
