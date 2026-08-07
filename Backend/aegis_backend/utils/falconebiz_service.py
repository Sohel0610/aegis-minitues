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
        # Use GET as per standard Falconebiz API patterns in this project
        response = requests.get(
            UPDATE_URL, 
            headers=headers, 
            proxies=PROXIES, 
            verify=False, 
            timeout=30
        )
        
        if response.status_code == 200:
            resp_text = response.text
            if "Update requested" in resp_text:
                return True, "Update requested successfully. Please check back in 2-5 minutes for the latest data."
            
            try:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    msg = data[0].get("success_msg") or data[0].get("message")
                    if msg: return True, msg
                return True, data.get("message") or "Refresh triggered successfully."
            except:
                return True, "Refresh triggered successfully."
        else:
            return False, f"API Error: {response.status_code}"
            
    except Exception as e:
        return False, f"Connection error: {str(e)}"
