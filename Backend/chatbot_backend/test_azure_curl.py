#!/usr/bin/env python3
"""
Test script for Azure curl approach
"""
import sys
import os

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from llm_layer.llm_client import chat_completion

def test_azure_curl():
    """Test Azure curl approach"""
    print("Testing Azure curl approach...")
    
    try:
        system_prompt = "You are a helpful assistant."
        user_prompt = "Hello, how are you?"
        
        response = chat_completion(system_prompt, user_prompt)
        print(f"Response: {response}")
        print("Azure curl approach: PASSED")
    except Exception as e:
        print(f"Azure curl approach: FAILED - {e}")

if __name__ == "__main__":
    test_azure_curl()