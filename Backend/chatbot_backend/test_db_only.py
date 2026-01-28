#!/usr/bin/env python3
"""
Test script for database selection feature without LLM
"""
import sys
import os

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from chat_orchestrator.router_logic import route_query
from data_layer.db_models import get_bse_session, get_sebi_session, get_rbi_session, BSENotification, SEBINotification, RBINotification

def test_database_routing():
    """Test database routing without LLM"""
    print("Testing database routing without LLM...")
    
    # Test BSE database routing
    print("\n1. Testing BSE database routing...")
    try:
        retrieval_method, results = route_query("Show me notifications for Tata Motors from 2025-08-10", database="bse")
        print(f"   Retrieval method: {retrieval_method}")
        print(f"   Number of results: {len(results)}")
        if results:
            print(f"   First result: {results[0].EntityName if hasattr(results[0], 'EntityName') else 'N/A'}")
        print("   BSE database routing: PASSED")
    except Exception as e:
        print(f"   BSE database routing: FAILED - {e}")
    
    # Test SEBI database routing
    print("\n2. Testing SEBI database routing...")
    try:
        retrieval_method, results = route_query("Show me regulatory updates from 01-09-2025", database="sebi")
        print(f"   Retrieval method: {retrieval_method}")
        print(f"   Number of results: {len(results)}")
        if results:
            print(f"   First result date: {results[0].date_key if hasattr(results[0], 'date_key') else 'N/A'}")
        print("   SEBI database routing: PASSED")
    except Exception as e:
        print(f"   SEBI database routing: FAILED - {e}")
    
    # Test RBI database routing
    print("\n3. Testing RBI database routing...")
    try:
        retrieval_method, results = route_query("Show me monetary policy updates from 01-09-2025", database="rbi")
        print(f"   Retrieval method: {retrieval_method}")
        print(f"   Number of results: {len(results)}")
        if results:
            print(f"   First result date: {results[0].run_date if hasattr(results[0], 'run_date') else 'N/A'}")
        print("   RBI database routing: PASSED")
    except Exception as e:
        print(f"   RBI database routing: FAILED - {e}")
    
    print("\nDatabase routing test complete!")

if __name__ == "__main__":
    test_database_routing()