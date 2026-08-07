from docx import Document
import os

# Path to the transcript file
file_path = r"AGE23L - Board Meeting - 3.00 p.m. IST, Monday, 27th October, 2025.docx"

# Check if file exists
if os.path.exists(file_path):
    print(f"File exists: {file_path}")
    doc = Document(file_path)
    
    # Print first 50 paragraphs
    print("\nFirst 50 paragraphs:")
    for i, para in enumerate(doc.paragraphs[:50]):
        print(f"{i+1}: {repr(para.text)}")
else:
    print(f"File not found: {file_path}")