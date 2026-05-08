import os
import io
import zipfile
from datetime import datetime
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter

# Styles
HEADER_FILL = PatternFill(start_color="75479C", end_color="75479C", fill_type="solid")
HEADER_FONT = Font(color="FFFFFF", bold=True, size=12)
SUBHEADER_FILL = PatternFill(start_color="F3F4F6", end_color="F3F4F6", fill_type="solid")
BORDER = Border(
    left=Side(style='thin', color="D1D5DB"),
    right=Side(style='thin', color="D1D5DB"),
    top=Side(style='thin', color="D1D5DB"),
    bottom=Side(style='thin', color="D1D5DB")
)

def format_sheet(ws):
    """Apply standard professional formatting to a sheet"""
    for row in ws.iter_rows():
        for cell in row:
            cell.border = BORDER
            cell.alignment = Alignment(vertical="center", wrap_text=True)
            if cell.row == 1:
                cell.fill = HEADER_FILL
                cell.font = HEADER_FONT
                cell.alignment = Alignment(horizontal="center", vertical="center")
    
    ws.row_dimensions[1].height = 35

def generate_director_excel(data):
    """
    Generates a formatted Excel workbook for a single director
    data: dict matching the output of director_full.py
    """
    wb = Workbook()
    
    # 1. Profile Sheet
    ws_profile = wb.active
    ws_profile.title = "Director Profile"
    
    profile_data = [
        ["Field", "Information"],
        ["DIN", data['director_info'].get('din')],
        ["Full Name", data['director_info'].get('name')],
        ["DIN Status", data['director_info'].get('din_status')],
        ["Gender", data['director_info'].get('gender')],
        ["Nationality", data['director_info'].get('nationality')],
        ["Date of Birth", data['profile'].get('date_of_birth')],
        ["PAN", data['profile'].get('pan')],
        ["Qualification", data['profile'].get('qualification')],
        ["Address", data['profile'].get('address')],
        ["Experience", data['profile'].get('experience')]
    ]
    
    for row in profile_data:
        ws_profile.append(row)
    
    # Column widths for Profile
    ws_profile.column_dimensions['A'].width = 25
    ws_profile.column_dimensions['B'].width = 80
    format_sheet(ws_profile)

    # 2. Associations Sheet
    ws_assoc = wb.create_sheet("Associations")
    ws_assoc.append(["CIN", "Company Name", "Designation", "Appt Date", "Status"])
    
    for assoc in data.get('associations', []):
        appt_date = assoc.get('appointment_date')
        status = assoc.get('company_status') or assoc.get('status') or "N/A"
        ws_assoc.append([
            assoc.get('cin') or "N/A",
            assoc.get('company_name') or "N/A",
            assoc.get('designation') or "Director",
            str(appt_date) if appt_date else "N/A",
            status
        ])
    
    ws_assoc.column_dimensions['A'].width = 25
    ws_assoc.column_dimensions['B'].width = 50
    ws_assoc.column_dimensions['C'].width = 25
    ws_assoc.column_dimensions['D'].width = 15
    ws_assoc.column_dimensions['E'].width = 15
    format_sheet(ws_assoc)

    # 3. Family Sheet
    ws_family = wb.create_sheet("Family Information")
    ws_family.append(["Relationship", "Name", "PAN"])
    
    family_rows = []
    
    # A. New Relational Data (Priority)
    members = data.get('family_members', [])
    for m in members:
        family_rows.append([
            m.get('relationship') or "Relative",
            m.get('full_name') or m.get('details') or "N/A",
            m.get('pan') or m.get('pan_number') or "N/A"
        ])
    
    # B. Master/Legacy Data (Fallback or Supplement)
    fam = data.get('family') or {}
    
    # Professional mapping of all fields seen in the JSON
    field_map = [
        ("Father", fam.get('father')),
        ("Mother", fam.get('mother')),
        ("Spouse", fam.get('section_2_77_ii')),
        ("Son", fam.get('son')),
        ("Son's Wife", fam.get('sons_wife')),
        ("Daughter", fam.get('daughter')),
        ("Daughter's Husband", fam.get('daughters_husband')),
        ("Brother", fam.get('brother')),
        ("Sister", fam.get('sister'))
    ]
    
    for rel, val in field_map:
        if val and str(val).lower() not in ["nil", "none", "n/a", ""]:
            # Handle multiple names in one string (commas or double spaces)
            # This makes the Excel look much cleaner
            names = []
            if "," in str(val):
                names = [n.strip() for n in str(val).split(",")]
            elif "  " in str(val): # Double space common in Gautam Adani's record
                names = [n.strip() for n in str(val).split("  ")]
            else:
                names = [str(val).strip()]
            
            for name in names:
                if name:
                    # Check if this name is already added via relational data to avoid duplicates
                    if not any(r[1].lower() == name.lower() for r in family_rows):
                        family_rows.append([rel, name, "N/A"])
    
    if not family_rows:
        ws_family.append(["N/A", "No family records found", "N/A"])
    else:
        for row in family_rows:
            ws_family.append(row)

    ws_family.column_dimensions['A'].width = 25
    ws_family.column_dimensions['B'].width = 50
    ws_family.column_dimensions['C'].width = 20
    format_sheet(ws_family)

    # Final touch: Row height for large text
    for ws in wb.worksheets:
        for row in range(1, ws.max_row + 1):
            ws.row_dimensions[row].height = 30 if row > 1 else 35

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output

def create_bulk_zip(all_directors_data):
    """
    Creates a ZIP folder containing individual Excel files
    all_directors_data: list of dicts (each from director_full.py)
    """
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'a', zipfile.ZIP_DEFLATED, False) as zip_file:
        for data in all_directors_data:
            name = data['director_info'].get('name', 'Unknown').replace(" ", "_")
            din = data['director_info'].get('din', '00000000')
            filename = f"Director_Disclosure_{din}_{name}.xlsx"
            
            excel_buffer = generate_director_excel(data)
            zip_file.writestr(filename, excel_buffer.getvalue())
            
    zip_buffer.seek(0)
    return zip_buffer
