#!/usr/bin/env python3
"""
Test script for mock LLM fallback
"""
import sys
import os

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from chat_orchestrator.orchestrator import process_user_query

def test_mock_llm_fallback():
    """Test mock LLM fallback"""
    print("Testing mock LLM fallback...")
    
    # Test BSE database query
    print("\n1. Testing BSE database query with mock LLM...")
    try:
        response, sources = process_user_query("Show me notifications for Tata Motors from 2025-08-10", "bse")
        print(f"   Response: {response}")
        print(f"   Sources: {sources}")
        print("   BSE query with mock LLM: PASSED")
    except Exception as e:
        print(f"   BSE query with mock LLM: FAILED - {e}")
    
    # Test SEBI database query
    print("\n2. Testing SEBI database query with mock LLM...")
    try:
        response, sources = process_user_query("Show me regulatory updates from 01-09-2025", "sebi")
        print(f"   Response: {response}")
        print(f"   Sources: {sources}")
        print("   SEBI query with mock LLM: PASSED")
    except Exception as e:
        print(f"   SEBI query with mock LLM: FAILED - {e}")
    
    # Test RBI database query
    print("\n3. Testing RBI database query with mock LLM...")
    try:
        response, sources = process_user_query("Show me monetary policy updates from 01-09-2025", "rbi")
        print(f"   Response: {response}")
        print(f"   Sources: {sources}")
        print("   RBI query with mock LLM: PASSED")
    except Exception as e:
        print(f"   RBI query with mock LLM: FAILED - {e}")
    
    print("\nMock LLM fallback test complete!")

if __name__ == "__main__":
    test_mock_llm_fallback()