"""
LLM Client Module
Wraps embedding and chat completion APIs
"""
from typing import List
from groq import Groq
import os
import json
import subprocess
import sys
from dotenv import load_dotenv
from config.llm_config import LLMConfig
 
# Load environment variables
load_dotenv()

def _ignore_missing_ssl_cert_file():
    ssl_cert_file = os.environ.get("SSL_CERT_FILE")
    if ssl_cert_file and not os.path.exists(ssl_cert_file):
        os.environ.pop("SSL_CERT_FILE", None)


# Initialize Groq client lazily so imports do not fail when Groq is not used.
groq_client = None


def _get_groq_client():
    global groq_client

    if groq_client is None:
        if not LLMConfig.GROQ_API_KEY:
            raise Exception("GROQ_API_KEY is not configured")

        _ignore_missing_ssl_cert_file()
        groq_client = Groq(api_key=LLMConfig.GROQ_API_KEY)

    return groq_client
 
def embed_text(text: str) -> List[float]:
    """
    Generate embedding for text using Groq-compatible embedding model
    Note: Groq doesn't currently support embeddings, so we'll use a placeholder
    In a real implementation, you would use OpenAI embeddings or similar
    """
    # Placeholder implementation - in real scenario, use actual embedding API
    # For now, we're using sentence-transformers in the indexing layer
    return [0.0] * 384  # MiniLM-L6-v2 embedding dimension
 
def chat_completion(system_prompt: str, user_prompt: str, model: str = None) -> str:
    """
    Get chat completion from configured LLM
    """
    if LLMConfig.is_groq_enabled():
        # Use Groq LLM
        if model is None:
            model = LLMConfig.GROQ_MODEL
       
        try:
            response = _get_groq_client().chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": user_prompt,
                    }
                ],
                model=model,
                temperature=0.7,
                max_tokens=1024,
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"Error getting LLM response from Groq: {str(e)}")
   
    elif LLMConfig.is_azure_enabled():
        # Use Azure OpenAI with curl (as previously working)
        try:
            import tempfile
                   
            # Create the prompt with system and user messages
            prompt_data = {
                "messages": [
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": user_prompt,
                    }
                ],
                "temperature": 0.2,
                "max_tokens": 1536,
                "top_p": 0.9
            }
                   
            # Create a temporary file for the prompt
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(prompt_data, f, indent=2)
                prompt_file = f.name
                   
            # Get Azure OpenAI configuration
            endpoint = LLMConfig.AZURE_ENDPOINT
            deployment = LLMConfig.AZURE_DEPLOYMENT
            api_key = LLMConfig.AZURE_API_KEY
                   
            # Build curl command
            api_url = f"{endpoint}/openai/deployments/{deployment}/chat/completions?api-version={LLMConfig.AZURE_API_VERSION}"
                   
            if os.name == 'nt':
                # Windows - use shell command with curl
                curl_command = f'curl -s -k -X POST "{api_url}" -H "Content-Type: application/json" -H "api-key: {api_key}" -d "@{prompt_file}"'
                result = subprocess.run(curl_command, capture_output=True, text=True, shell=True, timeout=30)
            else:
                # Unix/Linux/Mac - use direct subprocess call
                curl_command = [
                    'curl', '-s', '-k', '-X', 'POST', api_url,
                    '-H', 'Content-Type: application/json',
                    '-H', f'api-key: {api_key}',
                    '-d', f'@{prompt_file}'
                ]
                result = subprocess.run(curl_command, capture_output=True, text=True, timeout=30)
                   
            # Clean up the temporary file
            if os.path.exists(prompt_file):
                os.unlink(prompt_file)
                   
            if result.returncode != 0:
                error_msg = result.stderr if result.stderr else "Unknown error"
                raise Exception(f"Curl command failed with return code {result.returncode}: {error_msg}")
                   
            # Check if we got a response
            if not result.stdout:
                raise Exception("No response received from Azure OpenAI API")
                   
            # Parse the response
            try:
                response_data = json.loads(result.stdout)
            except json.JSONDecodeError as e:
                raise Exception(f"Failed to parse JSON response: {e}. Response: {result.stdout}")
                   
            # Check for error responses
            if "error" in response_data:
                error_message = response_data["error"]
                if isinstance(error_message, dict) and "message" in error_message:
                    raise Exception(f"Azure API error: {error_message['message']}. Full response: {response_data}")
                else:
                    raise Exception(f"Azure API error: {error_message}. Full response: {response_data}")
           
            # Extract content from response
            if "choices" in response_data and len(response_data["choices"]) > 0:
                if "message" in response_data["choices"][0] and "content" in response_data["choices"][0]["message"]:
                    content = response_data["choices"][0]["message"]["content"]
                    return content.strip() if content else "No summary available"
                else:
                    raise Exception(f"Unexpected response format: missing message content. Full response: {response_data}")
            else:
                raise Exception(f"Invalid LLM response format: no choices found. Full response: {response_data}")
                       
        except Exception as e:
            raise Exception(f"Error getting LLM response from Azure: {str(e)}")
   
    else:
        raise Exception(f"Unsupported LLM provider: {LLMConfig.LLM_PROVIDER}")
 
def generate_system_prompt() -> str:
    """
    Generate system prompt for the LLM
    """
    return """
You answer strictly using the provided notifications.
Do not invent information or add external context.
Return concise results focused on company, date, and nature.
Use plain ASCII only; bullets must be "-" and no Unicode bullets or dashes.
List the most recent items first.
If data is insufficient, say "Insufficient data".
Avoid advice, opinions, and external links.
"""
 
def format_notifications_for_llm(notifications: List) -> str:
    """
    Format notifications for LLM consumption
    """
    if not notifications:
        return "No relevant notifications found."
   
    formatted = ""
    for i, notification in enumerate(notifications, 1):
        # Handle both object and dictionary formats
        if hasattr(notification, 'entity_name'):
            # Object format (RegulatoryNotification)
            entity_name = notification.entity_name
            notice_date = notification.notice_date
            notice_type = notification.notice_type
            summary = notification.summary
            link = notification.link
        elif hasattr(notification, 'EntityName'):
            # Object format (DailyLog)
            entity_name = notification.EntityName
            notice_date = notification.Date
            notice_type = notification.Nature
            summary = notification.Summary
            link = notification.Link
        elif isinstance(notification, dict):
            # Dictionary format
            entity_name = notification.get('entity_name') or notification.get('EntityName', 'Unknown')
            notice_date = notification.get('notice_date') or notification.get('Date', 'Unknown')
            notice_type = notification.get('notice_type') or notification.get('Nature', '')
            summary = notification.get('summary') or notification.get('Summary', '')
            link = notification.get('link') or notification.get('Link', '')
        else:
            # Fallback
            entity_name = "Unknown"
            notice_date = "Unknown"
            notice_type = ""
            summary = ""
            link = ""
           
        formatted += f"[{i}] Entity: {entity_name}\n"
        formatted += f"    Date: {notice_date}\n"
        if notice_type:
            formatted += f"    Nature: {notice_type}\n"
        if summary:
            formatted += f"    Summary: {summary}\n"
        if link:
            formatted += f"    Link: {link}\n"
        formatted += "\n"
   
    return formatted
 
 
