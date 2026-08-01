import os
import sys

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(__file__))

from llm_utils import generate_and_save_summary

def test_summary_generation():
    """Test the summary generation functionality"""
    # Test with a sample document
    director_name = "Abdul Ishad Khan"
    din = "11280634"
    file_path = "Abdul Ishad Khan_MBP.docx"
    
    print(f"Generating summary for {director_name}...")
    summary = generate_and_save_summary(director_name, din, file_path)
    print(f"Summary generated:\n{summary}")
    
    # Test retrieving the summary from database
    print("\n" + "="*50)
    print("Testing retrieval from database...")
    
    from llm_utils import get_summary_from_db
    retrieved_summary = get_summary_from_db(file_path)
    print(f"Retrieved summary:\n{retrieved_summary}")

if __name__ == "__main__":
    test_summary_generation()