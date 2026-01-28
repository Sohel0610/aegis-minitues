import os
import sys
import time

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(__file__))

def regenerate_summaries():
    """Regenerate summaries using the improved extraction method"""
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
        
        # Generate summaries for each document
        for i, filename in enumerate(sorted(docx_files)):
            print(f"[{i+1}/{len(docx_files)}] Processing {filename}...")
            
            # Extract director name from filename
            director_name = filename.replace('_MBP.docx', '').replace('.docx', '').strip()
            din = 'N/A'  # Default value
            
            # Generate and save summary
            try:
                summary = generate_and_save_summary(director_name, din, filename)
                print(f"  ✓ Summary generated ({len(summary)} characters)")
                if len(summary) > 100:
                    print(f"    Summary preview: {summary[:100]}...")
            except Exception as e:
                print(f"  ✗ Error generating summary: {e}")
            
            # Add a small delay to avoid overwhelming any APIs
            time.sleep(0.5)
        
        print("\nFinished regenerating all summaries!")
        
    except Exception as e:
        print(f"Error regenerating summaries: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    regenerate_summaries()