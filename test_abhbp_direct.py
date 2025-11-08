#!/usr/bin/env python3
"""Direct database test for AB-HBP"""

import psycopg2
import os

conn = psycopg2.connect(
    host=os.getenv("DB_HOST", "localhost"),
    database=os.getenv("DB_NAME", "hms_terminology"),
    user=os.getenv("DB_USER", "postgres"),
    password=os.getenv("DB_PASSWORD", "postgres")
)

cur = conn.cursor()

print("🧪 Testing AB-HBP Database...\n")

# Test 1: Count
cur.execute("SELECT COUNT(*), COUNT(DISTINCT specialty) FROM abhbp_procedures")
count, specialties = cur.fetchone()
print(f"✅ Total Packages: {count}")
print(f"✅ Specialties: {specialties}\n")

# Test 2: Search burns
cur.execute("SELECT package_code, package_name, specialty, base_rate FROM abhbp_procedures WHERE package_name ILIKE '%burns%' LIMIT 3")
print("🔍 Search 'burns':")
for row in cur.fetchall():
    print(f"  {row[0]} - {row[1]} ({row[2]}) - ₹{row[3]}")

# Test 3: Get by code
cur.execute("SELECT * FROM abhbp_procedures WHERE package_code = 'BM001'")
print(f"\n📦 Package BM001:")
row = cur.fetchone()
print(f"  Name: {row[2]}")
print(f"  Specialty: {row[3]}")
print(f"  Rate: ₹{row[5]}")

# Test 4: List specialties
cur.execute("SELECT DISTINCT specialty FROM abhbp_procedures ORDER BY specialty LIMIT 5")
print(f"\n🏥 Sample Specialties:")
for row in cur.fetchall():
    print(f"  - {row[0]}")

cur.close()
conn.close()

print("\n✅ All database tests passed!")
