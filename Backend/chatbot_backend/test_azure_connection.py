#!/usr/bin/env python3
"""
Test script for Azure LLM connection
"""
import sys
import os
import json
import subprocess

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.llm_config import LLMConfig

def test_azure_connection():
    """Test Azure LLM connection"""
    print("Testing Azure LLM connection...")
    
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
    
    try:
        # Set environment variables for the script
        env = os.environ.copy()
        env["LLM_DEPLOYMENT"] = LLMConfig.AZURE_DEPLOYMENT
        env["LLM_ENDPOINT"] = LLMConfig.AZURE_ENDPOINT
        env["LLM_API_KEY"] = LLMConfig.AZURE_API_KEY
        
        print("\nCalling Azure LLM via shell script...")
        
        # Determine which script to use based on OS
        if sys.platform.startswith('win'):
            script_path = os.path.join(os.path.dirname(__file__), "llm_layer", "llm_client.bat")
            print(f"Using Windows batch script: {script_path}")
        else:
            script_path = os.path.join(os.path.dirname(__file__), "llm_layer", "llm_client.sh")
            print(f"Using Unix shell script: {script_path}")
        
        # Check if script exists
        if not os.path.exists(script_path):
            print(f"Script not found: {script_path}")
            return False
        
        # Call the script
        result = subprocess.run([
            script_path, 
            "test_prompt.json"
        ], capture_output=True, text=True, env=env, cwd=os.path.join(os.path.dirname(__file__), "llm_layer"))
        
        # Clean up temp file
        if os.path.exists("test_prompt.json"):
            os.remove("test_prompt.json")
        
        print(f"Return code: {result.returncode}")
        print(f"Stdout: {result.stdout}")
        print(f"Stderr: {result.stderr}")
        
        if result.returncode != 0:
            print(f"Error calling Azure LLM: {result.stderr}")
            return False
        else:
            print("Successfully connected to Azure LLM!")
            return True
            
    except Exception as e:
        print(f"Error testing Azure connection: {str(e)}")
        # Clean up temp file
        if os.path.exists("test_prompt.json"):
            os.remove("test_prompt.json")
        return False

if __name__ == "__main__":
    success = test_azure_connection()
    if success:
        print("\nAzure connection test: PASSED")
    else:
        print("\nAzure connection test: FAILED")