import requests
import time

def test_api_endpoint():
    """Test the FastAPI endpoint for document summaries"""
    
    try:
        # Test getting disclosures
        print("Testing disclosures endpoint...")
        response = requests.get('http://localhost:8000/api/directors-disclosures')
        if response.status_code == 200:
            disclosures = response.json()
            print(f"Found {disclosures['count']} disclosures")
            
            if disclosures['data']:
                # Test the first disclosure
                first_disclosure = disclosures['data'][0]
                disclosure_id = first_disclosure['id']
                print(f"\nTesting summary endpoint for disclosure ID: {disclosure_id}")
                
                # Test getting summary
                summary_response = requests.get(f'http://localhost:8000/api/directors-disclosures/{disclosure_id}/summary')
                if summary_response.status_code == 200:
                    summary_data = summary_response.json()
                    print(f"Director: {summary_data['director_name']}")
                    print(f"File: {summary_data['file_path']}")
                    print(f"Full text length: {len(summary_data['full_text'])} characters")
                    print(f"Summary length: {len(summary_data['summary'])} characters")
                    print(f"Summary preview: {summary_data['summary'][:200]}...")
                else:
                    print(f"Error getting summary: {summary_response.status_code}")
            else:
                print("No disclosures found")
        else:
            print(f"Error getting disclosures: {response.status_code}")
            
    except Exception as e:
        print(f"Error testing API endpoint: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_api_endpoint()