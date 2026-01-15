#!/bin/bash
# Download ICD-10-CM 2026 from CDC

set -e

echo "Downloading ICD-10-CM 2026..."
curl -L -o /tmp/icd10cm_codes_2026.zip https://www.cms.gov/files/zip/2026-code-descriptions-tabular-order.zip

echo "Extracting..."
unzip -o /tmp/icd10cm_codes_2026.zip -d /tmp/icd10_2026/

echo "Converting to CSV..."
python3 << 'EOF'
import csv
import os

# Find the codes file
codes_file = '/tmp/icd10_2026/icd10cm_codes_2026.txt'

if not os.path.exists(codes_file):
    print("ERROR: Could not find codes file")
    exit(1)

print(f"Processing: {codes_file}")

with open(codes_file, 'r', encoding='latin-1') as f, \
     open('/tmp/icd10_2026.csv', 'w', newline='') as out:
    
    writer = csv.writer(out)
    writer.writerow(['code', 'term'])
    
    for line in f:
        if len(line.strip()) > 0:
            # Format: CODE DESCRIPTION
            parts = line.strip().split(maxsplit=1)
            if len(parts) == 2:
                code = parts[0].replace('.', '')
                term = parts[1]
                writer.writerow([code, term])

print("CSV created: /tmp/icd10_2026.csv")
EOF

echo "Loading into database..."
psql -U samirkolhe -d medical_library << 'SQL'
BEGIN;

-- Truncate and reload (no backup needed)
TRUNCATE icd10_codes;

COPY icd10_codes(code, term) FROM '/tmp/icd10_2026.csv' WITH CSV HEADER;

-- Verify
SELECT 'Loaded ' || COUNT(*) || ' ICD-10-CM 2026 codes' FROM icd10_codes;

COMMIT;
SQL

echo "Cleaning up..."
rm -rf /tmp/icd10_2026/ /tmp/icd10cm_codes_2026.zip /tmp/icd10_2026.csv

echo "✅ ICD-10-CM 2026 loaded successfully"
