import requests
import time

def test_endpoints():
    """Test the new endpoints for document summaries"""
    
    # Test getting disclosures
    print("Testing disclosures endpoint...")
    response = requests.get('http://localhost:8000/api/directors-disclosures')
    if response.status_code == 200:
        disclosures = response.json()
        print(f"Found {disclosures['count']} disclosures")
        if disclosures['data']:
            first_disclosure = disclosures['data'][0]
            disclosure_id = first_disclosure['id']
            print(f"Testing with disclosure ID: {disclosure_id}")
            
            # Test getting summary
            print("\nTesting summary endpoint...")
            summary_response = requests.get(f'http://localhost:8000/api/directors-disclosures/{disclosure_id}/summary')
            if summary_response.status_code == 200:
                summary_data = summary_response.json()
                print(f"Summary: {summary_data['summary'][:100]}...")
            else:
                print(f"Error getting summary: {summary_response.status_code}")
            
            # Test generating summary
            print("\nTesting generate summary endpoint...")
            generate_response = requests.post(f'http://localhost:8000/api/directors-disclosures/{disclosure_id}/generate-summary')
            if generate_response.status_code == 200:
                generate_data = generate_response.json()
                print(f"Generate result: {generate_data['message']}")
                if generate_data['summary']:
                    print(f"Generated summary: {generate_data['summary'][:100]}...")
            else:
                print(f"Error generating summary: {generate_response.status_code}")
        else:
            print("No disclosures found")
    else:
        print(f"Error getting disclosures: {response.status_code}")

if __name__ == "__main__":
    test_endpoints()