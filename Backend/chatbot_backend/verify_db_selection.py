#!/usr/bin/env python3
"""
Verification script for database selection feature
"""
import sys
import os

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from chat_orchestrator.orchestrator import process_user_query
from chat_orchestrator.router_logic import route_query, execute_structured_query

def test_database_selection():
    """Test database selection functionality"""
    print("Testing database selection functionality...")
    
    # Test BSE database
    print("\n1. Testing BSE database query routing...")
    try:
        retrieval_method, results = route_query("Show me notifications for Tata Motors from 2025-08-10", database="bse")
        print(f"   Retrieval method: {retrieval_method}")
        print(f"   Number of results: {len(results)}")
        print("   BSE database routing: PASSED")
    except Exception as e:
        print(f"   BSE database routing: FAILED - {e}")
    
    # Test SEBI database
    print("\n2. Testing SEBI database query routing...")
    try:
        retrieval_method, results = route_query("Show me regulatory updates from 01-09-2025", database="sebi")
        print(f"   Retrieval method: {retrieval_method}")
        print(f"   Number of results: {len(results)}")
        print("   SEBI database routing: PASSED")
    except Exception as e:
        print(f"   SEBI database routing: FAILED - {e}")
    
    # Test RBI database
    print("\n3. Testing RBI database query routing...")
    try:
        retrieval_method, results = route_query("Show me monetary policy updates from 01-09-2025", database="rbi")
        print(f"   Retrieval method: {retrieval_method}")
        print(f"   Number of results: {len(results)}")
        print("   RBI database routing: PASSED")
    except Exception as e:
        print(f"   RBI database routing: FAILED - {e}")
    
    print("\nDatabase selection verification complete!")

if __name__ == "__main__":
    test_database_selection()