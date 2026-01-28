#!/usr/bin/env python3
"""
Mock test script for Azure LLM connection (without actual network calls)
"""
import sys
import os
import json

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.llm_config import LLMConfig

def mock_azure_connection_test():
    """Mock test for Azure LLM connection"""
    print("Mock testing Azure LLM connection...")
    
    # Check if Azure is enabled
    if not LLMConfig.is_azure_enabled():
        print("Azure LLM is not enabled. Please set LLM_PROVIDER=azure in .env file")
        return False
    
    print(f"Azure LLM is enabled")
    print(f"Endpoint: {LLMConfig.AZURE_ENDPOINT}")
    print(f"Deployment: {LLMConfig.AZURE_DEPLOYMENT}")
    print(f"API Version: {LLMConfig.AZURE_API_VERSION}")
    
    # Create a test prompt
    prompt_data = {
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful assistant."
            },
            {
                "role": "user",
                "content": "Hello, this is a test message."
            }
        ],
        "temperature": 0.7,
        "max_tokens": 100
    }
    
    # Write prompt to temporary file
    with open("test_prompt.json", "w") as f:
        json.dump(prompt_data, f)
    
    print("\nMock test: Creating prompt file...")
    print(f"Prompt file created: test_prompt.json")
    
    # Check if required environment variables are set
    env_vars = ["AZURE_DEPLOYMENT", "AZURE_ENDPOINT", "AZURE_API_KEY"]
    
    print("\nChecking environment variables:")
    all_vars_present = True
    for var in env_vars:
        value = getattr(LLMConfig, var)
        if value:
            print(f"  {var}: OK")
        else:
            print(f"  {var}: MISSING")
            all_vars_present = False
    
    # Clean up temp file
    if os.path.exists("test_prompt.json"):
        os.remove("test_prompt.json")
        print("\nCleaned up temporary file")
    
    if all_vars_present:
        print("\nMock Azure connection test: PASSED")
        print("All required configuration is present.")
        print("In a real environment, this would call the Azure LLM API.")
        return True
    else:
        print("\nMock Azure connection test: FAILED")
        print("Some required configuration is missing.")
        return False

def test_llm_client_import():
    """Test that we can import the LLM client"""
    print("\nTesting LLM client import...")
    try:
        from llm_layer.llm_client import chat_completion, generate_system_prompt
        print("LLM client import: PASSED")
        return True
    except Exception as e:
        print(f"LLM client import: FAILED - {str(e)}")
        return False

def test_config_loading():
    """Test that configuration loads correctly"""
    print("\nTesting configuration loading...")
    try:
        print(f"LLM Provider: {LLMConfig.LLM_PROVIDER}")
        print(f"Is Azure Enabled: {LLMConfig.is_azure_enabled()}")
        print(f"Is Groq Enabled: {LLMConfig.is_groq_enabled()}")
        print("Configuration loading: PASSED")
        return True
    except Exception as e:
        print(f"Configuration loading: FAILED - {str(e)}")
        return False

if __name__ == "__main__":
    print("Running mock Azure connection tests...")
    print("=" * 50)
    
    config_test = test_config_loading()
    import_test = test_llm_client_import()
    connection_test = mock_azure_connection_test()
    
    print("\n" + "=" * 50)
    print("MOCK TEST SUMMARY:")
    print(f"Configuration Loading: {'PASS' if config_test else 'FAIL'}")
    print(f"LLM Client Import: {'PASS' if import_test else 'FAIL'}")
    print(f"Azure Connection (Mock): {'PASS' if connection_test else 'FAIL'}")
    
    overall_success = config_test and import_test and connection_test
    print(f"Overall: {'PASS' if overall_success else 'FAIL'}")