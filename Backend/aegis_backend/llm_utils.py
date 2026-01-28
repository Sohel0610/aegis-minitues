import os
import sqlite3
import logging
import zipfile
from xml.etree import ElementTree as ET

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import docx, handle if not available
try:
    from docx import Document as DocxDocument
    DOCX_AVAILABLE = True
except ImportError:
    logger.warning("python-docx not available. Will use fallback text extraction.")
    DOCX_AVAILABLE = False

def extract_text_from_docx_fallback(file_path):
    """Extract text content from a DOCX file using fallback method (zip+xml)"""
    try:
        # DOCX files are essentially ZIP archives containing XML files
        with zipfile.ZipFile(file_path, 'r') as docx:
            # Read the main document XML
            xml_content = docx.read('word/document.xml')
            
            # Parse the XML
            tree = ET.fromstring(xml_content)
            
            # Extract text from paragraphs
            # Namespace for WordprocessingML
            ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
            
            paragraphs = tree.findall('.//w:p', ns)
            text_parts = []
            
            for paragraph in paragraphs:
                # Extract text from each paragraph
                texts = paragraph.findall('.//w:t', ns)
                paragraph_text = ''.join([t.text for t in texts if t.text])
                if paragraph_text.strip():
                    text_parts.append(paragraph_text)
            
            return '\n'.join(text_parts)
    except Exception as e:
        logger.error(f"Error extracting text from {file_path} using fallback method: {e}")
        return ""

def extract_text_from_docx(file_path):
    """Extract text content from a DOCX file"""
    if DOCX_AVAILABLE:
        try:
            doc = DocxDocument(file_path)
            content_parts = []
            
            # Extract all paragraphs
            for para in doc.paragraphs:
                if para.text.strip():
                    content_parts.append(para.text)
            
            # Extract tables if any
            if doc.tables:
                for table in doc.tables:
                    for row in table.rows:
                        row_text = " | ".join([cell.text.strip() for cell in row.cells])
                        content_parts.append(row_text)
            
            return "\n".join(content_parts)
        except Exception as e:
            logger.error(f"Error extracting text from {file_path} using python-docx: {e}")
            # Fall back to zip+xml method
            return extract_text_from_docx_fallback(file_path)
    else:
        # Use fallback method
        return extract_text_from_docx_fallback(file_path)

def generate_summary_with_groq(content, max_tokens=1000):
    """Generate a summary of the content using Groq LLM"""
    try:
        from groq import Groq
        
        # Initialize Groq client with API key
        api_key = os.environ.get('GROQ_API_KEY')
        if not api_key:
            logger.warning("GROQ_API_KEY not set, using default client")
            client = Groq()
        else:
            client = Groq(api_key=api_key)
        
        # Create the prompt with more specific formatting instructions
        prompt = f"""
        Please provide a concise summary of the following director's disclosure document. 
        Focus on the key information such as:
        - Director's name and DIN
        - Companies and positions held
        - Shareholding details
        - Other significant disclosures
        - Any important declarations or concerns
        
        Format requirements:
        1. Use plain text formatting only (no markdown, no special characters like *, +, #, etc.)
        2. Use section headers followed by a colon and a blank line (e.g., "Director's Information:\n")
        3. Use bullet points with the character "-" (e.g., "- Company Name - Position")
        4. For lists of companies, if there are many, list the first few and then say "and X other companies"
        5. Keep the summary concise and well-structured
        6. Do not use any markdown formatting, asterisks, or plus signs
        7. Do not include any extra formatting characters
        8. Each section should be clearly separated
        
        Example format:
        
        Director's Information:

        - Name: [Director Name]
        - DIN: [DIN Number]

        Companies and Positions Held:

        - [Company Name] - [Position]
        - [Company Name] - [Position]
        - and X other companies

        Shareholding Details:

        [Information about shareholding]

        Other Significant Disclosures:

        - [Disclosure 1]
        - [Disclosure 2]

        Important Declarations or Concerns:

        - [Declaration 1]
        - [Declaration 2]
        
        Document content:
        {content[:8000]}  # Limit content to avoid token limits
        """
        
        # Make API call to Groq
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert at summarizing corporate disclosure documents. Provide concise, structured summaries that highlight the most important information. Use plain text formatting with clear section headers and bullet points. Do not use markdown, asterisks, plus signs, or any special formatting characters. Use the bullet character '-' for lists. Each section should be clearly separated with a blank line after the section header."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,
            max_tokens=max_tokens,
            top_p=1,
            stream=True
        )
        
        # Extract the summary from the response
        summary = completion.choices[0].message.content
        return summary.strip() if summary else "No summary available"
        
    except Exception as e:
        logger.error(f"Error generating summary with Groq: {e}")
        return "Error generating summary with LLM"

def generate_summary_with_azure_openai(content, max_tokens=1000):
    """Generate a summary of the content using Azure OpenAI with curl"""
    try:
        import subprocess
        import json
        import tempfile
        import os
        
        # Get Azure OpenAI configuration from environment variables
        endpoint = os.environ.get('LLM_ENDPOINT')
        deployment = os.environ.get('LLM_DEPLOYMENT')
        api_key = os.environ.get('LLM_API_KEY')
        
        if not endpoint or not deployment or not api_key:
            raise Exception("Azure OpenAI configuration missing: LLM_ENDPOINT, LLM_DEPLOYMENT, or LLM_API_KEY not set")
        
        # Create the prompt with more specific formatting instructions
        prompt_data = {
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert at summarizing corporate disclosure documents. Provide concise, structured summaries that highlight the most important information. Use plain text formatting with clear section headers and bullet points. Do not use markdown, asterisks, plus signs, or any special formatting characters. Use the bullet character '-' for lists. Each section should be clearly separated with a blank line after the section header."
                },
                {
                    "role": "user",
                    "content": f"""
                    Please provide a concise summary of the following director's disclosure document. 
                    Focus on the key information such as:
                    - Director's name and DIN
                    - Companies and positions held
                    - Shareholding details
                    - Other significant disclosures
                    - Any important declarations or concerns
                    
                    Format requirements:
                    1. Use plain text formatting only (no markdown, no special characters like *, +, #, etc.)
                    2. Use section headers followed by a colon and a blank line (e.g., "Director's Information:\n")
                    3. Use bullet points with the character "-" (e.g., "- Company Name - Position")
                    4. For lists of companies, if there are many, list the first few and then say "and X other companies"
                    5. Keep the summary concise and well-structured
                    6. Do not use any markdown formatting, asterisks, or plus signs
                    7. Do not include any extra formatting characters
                    8. Each section should be clearly separated
                    
                    Example format:
                    
                    Director's Information:

                    - Name: [Director Name]
                    - DIN: [DIN Number]

                    Companies and Positions Held:

                    - [Company Name] - [Position]
                    - [Company Name] - [Position]
                    - and X other companies

                    Shareholding Details:

                    [Information about shareholding]

                    Other Significant Disclosures:

                    - [Disclosure 1]
                    - [Disclosure 2]

                    Important Declarations or Concerns:

                    - [Declaration 1]
                    - [Declaration 2]
                    
                    Document content:
                    {content[:8000]}  # Limit content to avoid token limits
                    """
                }
            ],
            "temperature": 0.3,
            "max_tokens": max_tokens
        }
        
        # Create a temporary file for the prompt
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(prompt_data, f, indent=2)
            prompt_file = f.name
        
        # Build curl command
        api_url = f"{endpoint}/openai/deployments/{deployment}/chat/completions?api-version=2023-05-15"
        
        if os.name == 'nt':
            # Windows - use shell command
            curl_command = f'curl -s -X POST "{api_url}" -H "Content-Type: application/json" -H "api-key: {api_key}" -d "@{prompt_file}"'
            result = subprocess.run(curl_command, capture_output=True, text=True, shell=True)
        else:
            # Unix/Linux/Mac - use direct subprocess call
            curl_command = [
                'curl', '-s', '-X', 'POST', api_url,
                '-H', 'Content-Type: application/json',
                '-H', f'api-key: {api_key}',
                '-d', f'@{prompt_file}'
            ]
            result = subprocess.run(curl_command, capture_output=True, text=True)
        
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
        
        # Extract content from response
        if "choices" in response_data and len(response_data["choices"]) > 0:
            if "message" in response_data["choices"][0] and "content" in response_data["choices"][0]["message"]:
                content = response_data["choices"][0]["message"]["content"]
                return content.strip() if content else "No summary available"
            else:
                raise Exception("Unexpected response format: missing message content")
        else:
            raise Exception("Invalid LLM response format: no choices found")
            
    except Exception as e:
        logger.error(f"Error generating summary with Azure OpenAI: {e}")
        return "Error generating summary with LLM"

def generate_summary(content, max_tokens=1000):
    """Generate a summary using either Groq or Azure OpenAI based on configuration"""
    # Check if we should use Groq
    use_groq = os.environ.get('USE_GROQ', 'true').lower() == 'true'
    
    if use_groq:
        try:
            from groq import Groq
            logger.info("Generating summary using Groq")
            return generate_summary_with_groq(content, max_tokens)
        except ImportError:
            logger.warning("Groq library not available, falling back to Azure OpenAI")
            logger.info("Generating summary using Azure OpenAI")
            return generate_summary_with_azure_openai(content, max_tokens)
    else:
        logger.info("Generating summary using Azure OpenAI")
        return generate_summary_with_azure_openai(content, max_tokens)

def save_summary_to_db(director_name, din, file_path, full_text, summary):
    """Save the full text and generated summary to the database"""
    try:
        db_path = os.path.join(os.path.dirname(__file__), 'directors_data.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if a record already exists for this file
        cursor.execute('''
            SELECT id FROM document_summaries WHERE file_path = ?
        ''', (file_path,))
        
        existing_record = cursor.fetchone()
        
        if existing_record:
            # Update existing record
            cursor.execute('''
                UPDATE document_summaries 
                SET director_name = ?, din = ?, full_text = ?, summary = ?, updated_at = CURRENT_TIMESTAMP
                WHERE file_path = ?
            ''', (director_name, din, full_text, summary, file_path))
        else:
            # Insert new record
            cursor.execute('''
                INSERT INTO document_summaries (director_name, din, file_path, full_text, summary)
                VALUES (?, ?, ?, ?, ?)
            ''', (director_name, din, file_path, full_text, summary))
        
        conn.commit()
        conn.close()
        logger.info(f"Full text and summary saved for {director_name}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving to database: {e}")
        return False

def get_summary_from_db(file_path):
    """Retrieve a summary from the database if it exists"""
    try:
        db_path = os.path.join(os.path.dirname(__file__), 'directors_data.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT summary FROM document_summaries WHERE file_path = ?
        ''', (file_path,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0]:
            return result[0]
        return None
        
    except Exception as e:
        logger.error(f"Error retrieving summary from database: {e}")
        return None

def generate_and_save_summary(director_name, din, file_path):
    """Extract full text, generate a summary, and save both to the database"""
    try:
        # Full file path
        full_file_path = os.path.join(os.path.dirname(__file__), "public", "Directors Discloser Output", file_path)
        
        # Check if file exists
        if not os.path.exists(full_file_path):
            return "Document file not found", "Document file not found"
        
        # Extract full text from document
        full_text = extract_text_from_docx(full_file_path)
        if not full_text.strip():
            full_text = f"Could not extract content from document - document may be empty or corrupted. File: {file_path}"
            summary = full_text
        else:
            # Generate summary using LLM (either Groq or Azure OpenAI)
            summary = generate_summary(full_text)
        
        # Save both full text and summary to database
        save_summary_to_db(director_name, din, file_path, full_text, summary)
        
        return full_text, summary
        
    except Exception as e:
        logger.error(f"Error generating and saving summary: {e}")
        error_msg = "Error processing document"
        return error_msg, error_msg