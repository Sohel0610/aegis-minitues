import os
import re
from docx import Document
from routes.director_data_analysis import extract_company_types_from_sections

def debug_company_types():
    """Debug the company type extraction logic with a sample document."""
    file_path = "public/Directors Discloser Output/Abdul Ishad Khan_MBP.docx"
    
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return
    
    # Load document
    doc = Document(file_path)
    
    # Convert document to text
    full_text = []
    for paragraph in doc.paragraphs:
        full_text.append(paragraph.text)
    
    full_text_str = "\n".join(full_text)
    
    print("=== FULL TEXT SAMPLE ===")
    print(full_text_str[:3000])  # Print first 3000 characters
    
    print("\n=== COMPANY TYPE EXTRACTION ===")
    
    # Extract company types
    company_types = extract_company_types_from_sections(full_text_str)
    
    print("Company Types Extracted:")
    for company_type, companies in company_types.items():
        print(f"  {company_type}: {len(companies)} companies")
        for company in companies:
            print(f"    - {company}")

if __name__ == "__main__":
    debug_company_types()