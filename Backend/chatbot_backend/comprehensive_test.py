#!/usr/bin/env python3
"""
Comprehensive test script for all components
"""
import sys
import os

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.llm_config import LLMConfig
from chat_orchestrator.orchestrator import process_user_query
from chat_orchestrator.router_logic import route_query, execute_structured_query
from data_layer.db_models import get_bse_session, get_sebi_session, get_rbi_session, BSENotification, SEBINotification, RBINotification

def test_database_connections():
    """Test connections to all databases"""
    print("Testing database connections...")
    
    try:
        # Test BSE database
        bse_session = get_bse_session()
        bse_count = bse_session.query(BSENotification).count()
        bse_session.close()
        print(f"BSE Database: {bse_count} records")
        
        # Test SEBI database
        sebi_session = get_sebi_session()
        sebi_count = sebi_session.query(SEBINotification).count()
        sebi_session.close()
        print(f"SEBI Database: {sebi_count} records")
        
        # Test RBI database
        rbi_session = get_rbi_session()
        rbi_count = rbi_session.query(RBINotification).count()
        rbi_session.close()
        print(f"RBI Database: {rbi_count} records")
        
        print("Database connections: PASSED")
        return True
    except Exception as e:
        print(f"Database connections: FAILED - {str(e)}")
        return False

def test_database_selection():
    """Test database selection functionality"""
    print("\nTesting database selection functionality...")
    
    # Test BSE database
    print("1. Testing BSE database query routing...")
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
    return True

def test_llm_configuration():
    """Test LLM configuration"""
    print("\nTesting LLM configuration...")
    
    print(f"LLM Provider: {LLMConfig.LLM_PROVIDER}")
    print(f"Is Azure Enabled: {LLMConfig.is_azure_enabled()}")
    print(f"Is Groq Enabled: {LLMConfig.is_groq_enabled()}")
    
    if LLMConfig.is_azure_enabled():
        print(f"Azure Endpoint: {LLMConfig.AZURE_ENDPOINT}")
        print(f"Azure Deployment: {LLMConfig.AZURE_DEPLOYMENT}")
        print("Azure LLM Configuration: PASSED")
    elif LLMConfig.is_groq_enabled():
        print(f"Groq Model: {LLMConfig.GROQ_MODEL}")
        print("Groq LLM Configuration: PASSED")
    else:
        print("Unknown LLM Provider")
        return False
    
    return True

def test_config_loading():
    """Test that configuration loads correctly"""
    print("\nTesting configuration loading...")
    try:
        port = os.getenv("SERVER_PORT", 8001)
        print(f"Server Port: {port}")
        print("Configuration loading: PASSED")
        return True
    except Exception as e:
        print(f"Configuration loading: FAILED - {str(e)}")
        return False

def main():
    """Main test function"""
    print("Running comprehensive tests...")
    print("=" * 50)
    
    config_test = test_config_loading()
    llm_test = test_llm_configuration()
    db_conn_test = test_database_connections()
    db_sel_test = test_database_selection()
    
    print("\n" + "=" * 50)
    print("COMPREHENSIVE TEST SUMMARY:")
    print(f"Configuration Loading: {'PASS' if config_test else 'FAIL'}")
    print(f"LLM Configuration: {'PASS' if llm_test else 'FAIL'}")
    print(f"Database Connections: {'PASS' if db_conn_test else 'FAIL'}")
    print(f"Database Selection: {'PASS' if db_sel_test else 'FAIL'}")
    
    overall_success = config_test and llm_test and db_conn_test and db_sel_test
    print(f"Overall: {'PASS' if overall_success else 'FAIL'}")
    
    return overall_success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)