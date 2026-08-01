from docx import Document
import os

def extract_text_from_docx(file_path):
    """Extract text content from a DOCX file"""
    try:
        doc = Document(file_path)
        text_content = "\n".join([para.text for para in doc.paragraphs])
        return text_content
    except Exception as e:
        return f"Error reading {file_path}: {str(e)}"

def analyze_teams_transcripts():
    """Analyze the structure of Teams meeting transcripts"""
    folder_path = "."
    transcript_files = [
        "AGE23L - Board Meeting - 3.00 p.m. IST, Monday, 27th October, 2025.docx",
        "AGEL_ Board Meeting on 28th October, 2025 - 11.00 a.m. onwards.docx",
        "ONLINE Link for 12th Adani Directors' Engagement Series (1).docx"
    ]
    
    analysis_results = {}
    
    for filename in transcript_files:
        file_path = os.path.join(folder_path, filename)
        if os.path.exists(file_path):
            print(f"\n{'='*80}")
            print(f"Analyzing: {filename}")
            print(f"{'='*80}")
            
            content = extract_text_from_docx(file_path)
            lines = content.split('\n')
            
            # Show first 50 lines to understand structure
            print("First 50 lines of content:")
            print("-" * 40)
            for i, line in enumerate(lines[:50]):
                print(f"{i+1:2d}: {line}")
                
            # Store for detailed analysis
            analysis_results[filename] = {
                'total_lines': len(lines),
                'first_50_lines': lines[:50],
                'content_sample': content[:2000]  # First 2000 characters
            }
            
            print(f"\nTotal lines in document: {len(lines)}")
            
            # Look for patterns
            timestamp_count = sum(1 for line in lines if ':' in line and any(char.isdigit() for char in line))
            speaker_count = sum(1 for line in lines if ':' in line and not line.startswith(' '))
            
            print(f"Lines with timestamps/speakers: {timestamp_count}")
            print(f"Speaker lines: {speaker_count}")
            
    return analysis_results

if __name__ == "__main__":
    results = analyze_teams_transcripts()