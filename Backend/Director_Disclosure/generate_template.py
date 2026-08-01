
import sys
import os
from pathlib import Path
from datetime import date

# Add current directory to path so we can import the generators
sys.path.append(os.path.dirname(__file__))

from dir8_generator import build_dir8, CompanyInfo, DirectorInfo, OtherCompany
from mbp1_generator import build_document, DirectorData

def create_templates():
    template_dir = Path(__file__).parent / "Templates"
    template_dir.mkdir(parents=True, exist_ok=True)
    
    print("Generating High-Fidelity Templates...")

    # 1. Generate DIR-8 Template
    co = CompanyInfo(
        cin="{{COMPANY_CIN}}",
        company_name="{{COMPANY_NAME}}",
        address="{{COMPANY_ADDRESS}}",
        auth_capital="{{NOMINAL_CAPITAL}}",
        paid_capital="{{PAID_UP_CAPITAL}}",
        signature_date="{{DATE}}"
    )
    di = DirectorInfo(
        din="{{DIRECTOR_DIN}}",
        name="{{DIRECTOR_NAME}}",
        father_name="{{FATHER_NAME}}",
        address="{{DIRECTOR_ADDRESS}}",
        designation="{{DIRECTOR_DESIGNATION}}"
    )
    # Add one dummy row for the table using the OtherCompany dataclass
    di.other_companies = [OtherCompany(
        com_name="{{OTHER_COMPANY_NAME}}",
        appointment_date="{{APPOINTMENT_DATE}}",
        cessation_date="{{CESSATION_DATE}}"
    )]
    
    dir8_doc = build_dir8(co, di)
    dir8_path = template_dir / "DIR-8_Template.docx"
    dir8_doc.save(str(dir8_path))
    print(f"  [OK] DIR-8 Template -> {dir8_path}")

    # 2. Generate MBP-1 Template
    dd = DirectorData(
        name="{{DIRECTOR_NAME}}",
        father_name="{{FATHER_NAME}}",
        address="{{DIRECTOR_ADDRESS}}",
        din="{{DIRECTOR_DIN}}",
        primary_company="{{COMPANY_NAME}}",
        signature_date="{{DATE}}",
        signature_place="Ahmedabad"
    )
    # MBP-1 uses list of dictionaries for associations
    dd.associations = [{
        "com_name": "{{OTHER_COMPANY_NAME}}",
        "designation": "{{DESIGNATION}}",
        "appointment": "{{DATE}}"
    }]
    # MBP-1 uses list of dictionaries for relatives
    dd.rel_bodies_corporate = [{
        "name": "{{BODY_CORPORATE_NAME}}",
        "interest": "{{NATURE_OF_INTEREST}}"
    }]
    
    mbp1_doc = build_document(dd, include_annexure=True)
    mbp1_path = template_dir / "MBP-1_Template.docx"
    mbp1_doc.save(str(mbp1_path))
    print(f"  [OK] MBP-1 Template -> {mbp1_path}")

if __name__ == "__main__":
    create_templates()
