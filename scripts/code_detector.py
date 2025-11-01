import re

def detect_icd_version(code: str) -> str:
    """Detect if code is ICD-10 or ICD-11"""
    # ICD-10: Letter + digits (e.g., E10.9, I10, J18.9)
    if re.match(r'^[A-Z]\d{2,3}(\.\d+)?$', code):
        return "ICD-10"
    
    # ICD-11: Optional digits + Letter + digits (e.g., 5A11, 6A70, BA00)
    if re.match(r'^\d*[A-Z]\d{2}', code) and not re.match(r'^[A-Z]\d{2,3}(\.\d+)?$', code):
        return "ICD-11"
    
    return "Unknown"

# Test examples
codes = ["E10.9", "5A11", "I10", "6A70", "J18.9", "BA00"]
for code in codes:
    print(f"{code}: {detect_icd_version(code)}")