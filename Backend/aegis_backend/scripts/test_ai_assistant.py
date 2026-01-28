import os
import sys
import json
from dotenv import load_dotenv

# Add the routes directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'routes'))

# Load environment variables
load_dotenv()

print("Environment variables:")
print(f"USE_GROQ: {os.environ.get('USE_GROQ', 'Not set')}")
print(f"GROQ_API_KEY: {os.environ.get('GROQ_API_KEY', 'Not set')[:10]}...")  # Show only first 10 chars for security

# Test the AI assistant functionality
from routes.ai_assistant import router
print("\nAI Assistant module loaded successfully")

# Check if Groq is properly configured
try:
    from groq import Groq
    print("Groq library imported successfully")
    
    # Test Groq client initialization
    client = Groq()
    print("Groq client initialized successfully")
except Exception as e:
    print(f"Error with Groq: {e}")

print("\nTest completed")