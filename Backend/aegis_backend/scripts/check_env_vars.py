import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_env_vars():
    """Check that environment variables are loaded correctly"""
    print("Environment Variables:")
    print(f"USE_GROQ: {os.environ.get('USE_GROQ', 'Not set')}")
    print(f"GROQ_API_KEY: {os.environ.get('GROQ_API_KEY', 'Not set')[:10]}...")  # Show first 10 chars for security
    print(f"LLM_ENDPOINT: {os.environ.get('LLM_ENDPOINT', 'Not set')}")
    print(f"LLM_DEPLOYMENT: {os.environ.get('LLM_DEPLOYMENT', 'Not set')}")
    
    # Check which LLM provider is configured
    use_groq = os.environ.get('USE_GROQ', 'true').lower() == 'true'
    if use_groq:
        print("\nCurrently configured to use: Groq")
    else:
        print("\nCurrently configured to use: Azure OpenAI")

if __name__ == "__main__":
    check_env_vars()