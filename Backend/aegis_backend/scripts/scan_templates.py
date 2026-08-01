"""
Scan all .docx template files and extract the sample company names,
director names, dates, and meeting numbers embedded in them.
This helps us understand what hardcoded text exists in each template.
"""
import os
import re
import json
from docx import Document

templates_dir = os.path.join(os.path.dirname(__file__), "..", "public", "templates")

# Only scan original templates, not generated meeting_minutes_ files
original_templates = [
    f for f in os.listdir(templates_dir)
    if f.endswith('.docx') and not f.startswith('meeting_minutes_')
]

results = {}

for fname in sorted(original_templates):
    fpath = os.path.join(templates_dir, fname)
    try:
        doc = Document(fpath)
        full_text = "\n".join([p.text for p in doc.paragraphs])
        
        # Extract company-like names (ALL CAPS words with LIMITED/LTD)
        company_patterns = re.findall(r'[A-Z][A-Z\s\(\)\-\']+(?:LIMITED|LTD\.?)', full_text)
        companies = list(set([c.strip() for c in company_patterns if len(c.strip()) > 10]))
        
        # Extract person names (Mr./Mrs./Ms./Shri followed by names)
        person_patterns = re.findall(r'(?:Mr\.|Mrs\.|Ms\.|Shri|Smt\.)\s+[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){1,3}', full_text)
        persons = list(set([p.strip() for p in person_patterns]))
        
        # Extract DIN numbers (8-digit numbers)
        din_patterns = re.findall(r'\b(\d{8})\b', full_text)
        dins = list(set(din_patterns))
        
        # Extract dates in various formats
        date_patterns_1 = re.findall(r'\d{1,2}(?:ST|ND|RD|TH)\s+[A-Z]+\s+\d{4}', full_text, re.IGNORECASE)
        date_patterns_2 = re.findall(r'\d{2}\.\d{2}\.\d{4}', full_text)
        date_patterns_3 = re.findall(r'\d{1,2}(?:st|nd|rd|th)\s+(?:day of\s+)?[A-Za-z]+,?\s+\d{4}', full_text, re.IGNORECASE)
        dates = list(set(date_patterns_1 + date_patterns_2 + date_patterns_3))
        
        # Extract meeting numbers (ordinal words like FIFTY NINTH, EIGHTY SEVENTH etc)
        ordinal_patterns = re.findall(
            r'(?:FIRST|SECOND|THIRD|FOURTH|FIFTH|SIXTH|SEVENTH|EIGHTH|NINTH|TENTH|'
            r'ELEVENTH|TWELFTH|THIRTEENTH|FOURTEENTH|FIFTEENTH|SIXTEENTH|SEVENTEENTH|'
            r'EIGHTEENTH|NINETEENTH|TWENTIETH|THIRTIETH|FORTIETH|FIFTIETH|SIXTIETH|'
            r'SEVENTIETH|EIGHTIETH|NINETIETH|HUNDREDTH|'
            r'TWENTY[\s-]?(?:FIRST|SECOND|THIRD|FOURTH|FIFTH|SIXTH|SEVENTH|EIGHTH|NINTH)|'
            r'THIRTY[\s-]?(?:FIRST|SECOND|THIRD|FOURTH|FIFTH|SIXTH|SEVENTH|EIGHTH|NINTH)|'
            r'FORTY[\s-]?(?:FIRST|SECOND|THIRD|FOURTH|FIFTH|SIXTH|SEVENTH|EIGHTH|NINTH)|'
            r'FIFTY[\s-]?(?:FIRST|SECOND|THIRD|FOURTH|FIFTH|SIXTH|SEVENTH|EIGHTH|NINTH)|'
            r'SIXTY[\s-]?(?:FIRST|SECOND|THIRD|FOURTH|FIFTH|SIXTH|SEVENTH|EIGHTH|NINTH)|'
            r'SEVENTY[\s-]?(?:FIRST|SECOND|THIRD|FOURTH|FIFTH|SIXTH|SEVENTH|EIGHTH|NINTH)|'
            r'EIGHTY[\s-]?(?:FIRST|SECOND|THIRD|FOURTH|FIFTH|SIXTH|SEVENTH|EIGHTH|NINTH)|'
            r'NINETY[\s-]?(?:FIRST|SECOND|THIRD|FOURTH|FIFTH|SIXTH|SEVENTH|EIGHTH|NINTH))',
            full_text
        )
        ordinals = list(set(ordinal_patterns))
        
        # Extract numeric ordinals like 59th, 87th
        num_ordinals = re.findall(r'\b(\d+(?:ST|ND|RD|TH))\b', full_text, re.IGNORECASE)
        num_ordinals = list(set([n.upper() for n in num_ordinals]))
        
        results[fname] = {
            "companies": sorted(companies),
            "persons": sorted(persons),
            "dins": sorted(dins),
            "dates": sorted(dates),
            "ordinal_meeting_nums": sorted(ordinals),
            "numeric_ordinals": sorted(num_ordinals),
        }
        
    except Exception as e:
        results[fname] = {"error": str(e)}

# Print results
for fname, data in results.items():
    print(f"\n{'='*80}")
    print(f"TEMPLATE: {fname}")
    print(f"{'='*80}")
    if "error" in data:
        print(f"  ERROR: {data['error']}")
        continue
    for key, values in data.items():
        if values:
            print(f"  {key}:")
            for v in values:
                print(f"    - {v}")

# Save JSON for programmatic use
output_path = os.path.join(os.path.dirname(__file__), "template_scan_results.json")
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)
print(f"\n\nJSON saved to: {output_path}")
