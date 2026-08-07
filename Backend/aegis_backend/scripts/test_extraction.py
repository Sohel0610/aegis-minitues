import os
import sys

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(__file__))

from llm_utils import extract_text_from_docx

def test_extraction():
    """Test the text extraction method"""
    try:
        # Test with a sample document
        file_path = os.path.join(os.path.dirname(__file__), "public", "Directors Discloser Output", "Abdul Ishad Khan_MBP.docx")
        
        if os.path.exists(file_path):
            print(f"Testing extraction from {file_path}")
            content = extract_text_from_docx(file_path)
            print(f"Extracted {len(content)} characters")
            print(f"First 200 characters: {content[:200]}")
        else:
            print(f"File not found: {file_path}")
            
    except Exception as e:
        print(f"Error testing extraction: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_extraction()