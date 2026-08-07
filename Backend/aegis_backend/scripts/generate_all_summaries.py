import os
import sys
import requests
import time

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(__file__))

def generate_all_summaries():
    """Generate summaries for all disclosure documents"""
    try:
        # Get all disclosures
        print("Fetching disclosures...")
        response = requests.get('http://localhost:8000/api/directors-disclosures')
        
        if response.status_code != 200:
            print(f"Error fetching disclosures: {response.status_code}")
            return
            
        disclosures = response.json()
        print(f"Found {disclosures['count']} disclosures")
        
        # Generate summaries for each disclosure
        for i, disclosure in enumerate(disclosures['data']):
            disclosure_id = disclosure['id']
            director_name = disclosure['director_name']
            
            print(f"\n[{i+1}/{disclosures['count']}] Generating summary for {director_name}...")
            
            # Check if summary already exists
            summary_response = requests.get(f'http://localhost:8000/api/directors-disclosures/{disclosure_id}/summary')
            if summary_response.status_code == 200:
                summary_data = summary_response.json()
                # If summary already exists and is not a placeholder, skip
                if summary_data['id'] > 0 and not summary_data['summary'].startswith('Summary not yet generated'):
                    print(f"  Summary already exists, skipping...")
                    continue
            
            # Generate new summary
            generate_response = requests.post(f'http://localhost:8000/api/directors-disclosures/{disclosure_id}/generate-summary')
            if generate_response.status_code == 200:
                generate_data = generate_response.json()
                if generate_data['success']:
                    print(f"  ✓ Summary generated successfully")
                else:
                    print(f"  ✗ Failed to generate summary: {generate_data['message']}")
            else:
                print(f"  ✗ Error generating summary: {generate_response.status_code}")
            
            # Add a small delay to avoid overwhelming the API
            time.sleep(1)
            
        print("\nFinished processing all disclosures!")
        
    except Exception as e:
        print(f"Error generating summaries: {e}")

if __name__ == "__main__":
    generate_all_summaries()