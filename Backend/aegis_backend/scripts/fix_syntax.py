import re

with open('Backend/aegis_backend/routes/servicenow_reconciliation.py', 'r') as f:
    code = f.read()

# Replace the incorrect literal string 
code = code.replace(r"if \'conn\' in locals():", "if 'conn' in locals():")
code = code.replace(r"if \\'conn\\' in locals():", "if 'conn' in locals():")
code = code.replace("if \\'conn\\' in locals():", "if 'conn' in locals():")

with open('Backend/aegis_backend/routes/servicenow_reconciliation.py', 'w') as f:
    f.write(code)

print("Fixed")
