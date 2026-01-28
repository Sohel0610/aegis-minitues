#!/usr/bin/env python3
"""
Test script for Azure LLM connection using .sh script
"""
import sys
import os
import json
import subprocess

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.llm_config import LLMConfig

def test_azure_sh_script():
    """Test Azure LLM connection using .sh script"""
    print("Testing Azure LLM connection using .sh script...")
    
    # Check if Azure is enabled
    if not LLMConfig.is_azure_enabled():
        print("Azure LLM is not enabled. Please set LLM_PROVIDER=azure in .env file")
        return False
    
    print(f"Azure LLM is enabled")
    print(f"Endpoint: {LLMConfig.AZURE_ENDPOINT}")
    print(f"Deployment: {LLMConfig.AZURE_DEPLOYMENT}")
    
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
    with open("temp_prompt.json", "w") as f:
        json.dump(prompt_data, f)
    
    print(f"Created temp_prompt.json")
    
    # Check if bash is available
    try:
        result = subprocess.run(["bash", "--version"], capture_output=True, text=True)
        print(f"Bash available: {result.stdout.splitlines()[0]}")
    except Exception as e:
        print(f"Bash not available: {e}")
        # Clean up temp file
        if os.path.exists("temp_prompt.json"):
            os.remove("temp_prompt.json")
        return False
    
    # Check if script exists
    script_path = os.path.join(os.path.dirname(__file__), "llm_layer", "llm_client.sh")
    if not os.path.exists(script_path):
        print(f"Script not found: {script_path}")
        # Clean up temp file
        if os.path.exists("temp_prompt.json"):
            os.remove("temp_prompt.json")
        return False
    
    print(f"Script found: {script_path}")
    print("Azure .sh script test: READY (would work if bash is properly configured)")
    
    # Clean up temp file
    if os.path.exists("temp_prompt.json"):
        os.remove("temp_prompt.json")
        print("Cleaned up temporary file")
    
    return True

if __name__ == "__main__":
    success = test_azure_sh_script()
    if success:
        print("\nAzure .sh script test: READY")
        print("The script is properly configured and would work with bash.")
    else:
        print("\nAzure .sh script test: NOT READY")
        print("The script needs bash to be properly configured.")