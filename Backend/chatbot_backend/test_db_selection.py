#!/usr/bin/env python3
"""
Test script for database selection feature
"""
import requests
import json

# Base URL for the API
BASE_URL = "http://localhost:8000"

def test_database_selection():
    """Test database selection feature"""
    print("Testing database selection feature...")
    
    # Test BSE database
    print("\n1. Testing BSE database...")
    chat_data = {
        "message": "Show me notifications for Tata Motors from 2025-08-10",
        "session_id": "test_session_bse",
        "database": "bse"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/chat/message",
            json=chat_data,
            headers={"Content-Type": "application/json"}
        )
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Response: {result['response'][:200]}...")  # First 200 chars
            print(f"Database Used: {result['database_used']}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test SEBI database
    print("\n2. Testing SEBI database...")
    chat_data = {
        "message": "Show me regulatory updates from 01-09-2025",
        "session_id": "test_session_sebi",
        "database": "sebi"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/chat/message",
            json=chat_data,
            headers={"Content-Type": "application/json"}
        )
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Response: {result['response'][:200]}...")  # First 200 chars
            print(f"Database Used: {result['database_used']}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test RBI database
    print("\n3. Testing RBI database...")
    chat_data = {
        "message": "Show me monetary policy updates from 01-09-2025",
        "session_id": "test_session_rbi",
        "database": "rbi"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/chat/message",
            json=chat_data,
            headers={"Content-Type": "application/json"}
        )
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Response: {result['response'][:200]}...")  # First 200 chars
            print(f"Database Used: {result['database_used']}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_database_selection()