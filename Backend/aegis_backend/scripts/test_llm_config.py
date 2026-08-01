import os
import sys

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(__file__))

from llm_utils import generate_summary

def test_llm_config():
    """Test the LLM configuration"""
    # Check current configuration
    use_groq = os.environ.get('USE_GROQ', 'true').lower() == 'true'
    print(f"USE_GROQ: {use_groq}")
    
    if use_groq:
        print("Currently configured to use Groq")
    else:
        print("Currently configured to use Azure OpenAI")
    
    # Test with a simple prompt
    test_content = "This is a test document for director Abhishek Kumar with DIN 12345678. He is a director in Company A and Company B."
    
    print("\nGenerating test summary...")
    summary = generate_summary(test_content, max_tokens=500)
    print("Generated summary:")
    print(summary)

if __name__ == "__main__":
    test_llm_config()