from docx import Document
import re

# Load a sample document
doc_path = "public/Directors Discloser Output/Abdul Ishad Khan_MBP.docx"
doc = Document(doc_path)

# Convert document to text
full_text = []
for paragraph in doc.paragraphs:
    full_text.append(paragraph.text)

full_text_str = "\n".join(full_text)

print("=== FULL TEXT SAMPLE ===")
print(full_text_str[:2000])  # Print first 2000 characters

print("\n=== SECTION EXTRACTION ===")

# Look for section patterns
# Pattern for Public Limited Companies section
public_pattern = r"\(A\)\s*Public Limited Companies:.*?(?=\n\([B-Z]\)|$)"
public_match = re.search(public_pattern, full_text_str, re.DOTALL | re.IGNORECASE)
if public_match:
    public_section = public_match.group(0)
    print("Public Section Found:")
    print(public_section)
    # Extract company names (lines with "LIMITED")
    public_companies = re.findall(r"([A-Z0-9\s&.,'-]*LIMITED)", public_section)
    print("Public Companies Found:")
    for company in public_companies:
        if company.strip():
            print(f"  - {company.strip()}")
else:
    print("No Public Section Found")

# Pattern for Private Limited Companies which are subsidiary(ies) of Public Companies
private_subsidiary_pattern = r"\(B\)\s*Private Limited Companies which are subsidiary\(ies\) of Public Companies:.*?(?=\n\([C-Z]\)|$)"
private_subsidiary_match = re.search(private_subsidiary_pattern, full_text_str, re.DOTALL | re.IGNORECASE)
if private_subsidiary_match:
    private_subsidiary_section = private_subsidiary_match.group(0)
    print("\nPrivate Subsidiary Section Found:")
    print(private_subsidiary_section)
    # Extract company names (lines with "LIMITED") unless it's "NIL"
    if "NIL" not in private_subsidiary_section.upper():
        private_subsidiary_companies = re.findall(r"([A-Z0-9\s&.,'-]*LIMITED)", private_subsidiary_section)
        print("Private Subsidiary Companies Found:")
        for company in private_subsidiary_companies:
            if company.strip():
                print(f"  - {company.strip()}")
    else:
        print("Private Subsidiary Section contains NIL")
else:
    print("\nNo Private Subsidiary Section Found")

# Pattern for Private Limited Companies which are not subsidiary(ies) of Public Companies
private_non_subsidiary_pattern = r"\(C\)\s*Private Limited Companies which are not subsidiary\(ies\) of Public Companies:.*?(?=\n\([D-Z]\)|$)"
private_non_subsidiary_match = re.search(private_non_subsidiary_pattern, full_text_str, re.DOTALL | re.IGNORECASE)
if private_non_subsidiary_match:
    private_non_subsidiary_section = private_non_subsidiary_match.group(0)
    print("\nPrivate Non-Subsidiary Section Found:")
    print(private_non_subsidiary_section)
    # Extract company names (lines with "LIMITED") unless it's "NIL"
    if "NIL" not in private_non_subsidiary_section.upper():
        private_non_subsidiary_companies = re.findall(r"([A-Z0-9\s&.,'-]*LIMITED)", private_non_subsidiary_section)
        print("Private Non-Subsidiary Companies Found:")
        for company in private_non_subsidiary_companies:
            if company.strip():
                print(f"  - {company.strip()}")
    else:
        print("Private Non-Subsidiary Section contains NIL")
else:
    print("\nNo Private Non-Subsidiary Section Found")