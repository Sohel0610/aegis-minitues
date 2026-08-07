import requests
import sys

# Credentials provided by IT
CLIENT_ID = "5213b09f-38b2-4936-8f31-d4c8c1f9ecb5"
TENANT_ID = "04c72f56-1848-46a2-8167-8e5d36510cbc"
CLIENT_SECRET = "3tC8Q~kFYV0m5whHcMEJr6G_esL42yPW1M_rPdxO"
REDIRECT_URI = "https://aegis.adani.com/api/auth/callback"

def test_azure_sso():
    print(f"--- Azure AD SSO Validation Test ---")
    print(f"Tenant ID: {TENANT_ID}")
    print(f"Client ID: {CLIENT_ID}")
    
    # URL for token exchange
    token_url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
    
    # Testing Client Credentials Flow to validate Secret
    print("\n[Step 1] Testing Client Credentials Flow...")
    payload = {
        'grant_type': 'client_credentials',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'scope': 'https://graph.microsoft.com/.default'
    }
    
    try:
        response = requests.post(token_url, data=payload)
        if response.status_code == 200:
            print("âœ… SUCCESS: Client Credentials validated. Token received.")
            token_data = response.json()
            access_token = token_data.get("access_token")
            print(f"Access Token (first 20 chars): {access_token[:20]}...")
        else:
            print(f"â Œ FAILED: Could not get token.")
            print(f"Response: {response.text}")
            return
    except Exception as e:
        print(f"â Œ ERROR during request: {e}")
        return

    # Generate sample Auth URL (for user verification)
    print("\n[Step 2] Generating Authorization URL for Manual Check...")
    auth_url = (
        f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/authorize?"
        f"client_id={CLIENT_ID}&"
        "response_type=code&"
        f"redirect_uri={REDIRECT_URI}&"
        "scope=openid profile email&"
        "response_mode=query&"
        "state=test_state_123"
    )
    print(f"Authorization URL:\n{auth_url}")
    print("\n--- End of Validation ---")

if __name__ == "__main__":
    test_azure_sso()
