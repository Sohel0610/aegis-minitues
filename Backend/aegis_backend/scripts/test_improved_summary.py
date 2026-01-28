import os
import sys

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(__file__))

from llm_utils import generate_and_save_summary

def test_improved_summary():
    """Test the improved summary generation"""
    try:
        # Test with a sample document
        filename = "Abdul Ishad Khan_MBP.docx"
        director_name = "Abdul Ishad Khan"
        din = "N/A"
        
        print(f"Generating improved summary for {director_name}...")
        
        # Generate and save full text and summary
        full_text, summary = generate_and_save_summary(director_name, din, filename)
        
        print(f"Full text length: {len(full_text)} characters")
        print(f"Summary length: {len(summary)} characters")
        print("\nGenerated Summary:")
        print("=" * 50)
        print(summary)
        print("=" * 50)
        
    except Exception as e:
        print(f"Error testing improved summary: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_improved_summary()