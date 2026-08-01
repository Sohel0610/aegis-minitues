import os
import sys
import time

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(__file__))

def process_all_documents():
    """Process all documents and populate the database with full text and summaries"""
    try:
        # Import our utilities
        from llm_utils import generate_and_save_summary
        
        # Path to the disclosures directory
        disclosures_dir = os.path.join(os.path.dirname(__file__), "public", "Directors Discloser Output")
        
        if not os.path.exists(disclosures_dir):
            print("Disclosures directory not found")
            return
            
        # Get all docx files
        docx_files = [f for f in os.listdir(disclosures_dir) 
                     if f.endswith('.docx') and not f.startswith('~$')]
        
        print(f"Found {len(docx_files)} disclosure documents")
        
        # Process each document
        for i, filename in enumerate(sorted(docx_files)):
            print(f"[{i+1}/{len(docx_files)}] Processing {filename}...")
            
            # Extract director name from filename
            director_name = filename.replace('_MBP.docx', '').replace('.docx', '').strip()
            din = 'N/A'  # Default value
            
            # Generate and save full text and summary
            try:
                full_text, summary = generate_and_save_summary(director_name, din, filename)
                print(f"  ✓ Processed successfully")
                print(f"    Full text: {len(full_text)} characters")
                print(f"    Summary: {len(summary)} characters")
                if len(summary) > 100:
                    print(f"    Summary preview: {summary[:100]}...")
            except Exception as e:
                print(f"  ✗ Error processing: {e}")
            
            # Add a 10-second delay to avoid overwhelming the API
            print("  Waiting 10 seconds before next request...")
            time.sleep(4)
        
        print("\nFinished processing all documents!")
        
    except Exception as e:
        print(f"Error processing documents: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    process_all_documents()