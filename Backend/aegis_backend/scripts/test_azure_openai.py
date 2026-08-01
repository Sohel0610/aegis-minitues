import os
import sys

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(__file__))

from llm_utils import generate_summary_with_azure_openai

def test_azure_openai():
    """Test the Azure OpenAI configuration"""
    try:
        # Test with a simple prompt
        test_content = "This is a test document for director Abhishek Kumar with DIN 12345678. He is a director in Company A and Company B."
        
        print("Testing Azure OpenAI configuration...")
        print(f"LLM_ENDPOINT: {os.environ.get('LLM_ENDPOINT', 'Not set')}")
        print(f"LLM_DEPLOYMENT: {os.environ.get('LLM_DEPLOYMENT', 'Not set')}")
        print(f"LLM_API_KEY: {'Set' if os.environ.get('LLM_API_KEY') else 'Not set'}")
        
        print("\nGenerating test summary with Azure OpenAI...")
        summary = generate_summary_with_azure_openai(test_content, max_tokens=500)
        print("Generated summary:")
        print(summary)
        
    except Exception as e:
        print(f"Error testing Azure OpenAI: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_azure_openai()