#!/usr/bin/env python3
"""Quick test for AB-HBP API"""

import requests

BASE_URL = "http://localhost:8001"

print("🧪 Testing AB-HBP API...\n")

# Test 1: Search
print("1️⃣ Search for 'burns':")
r = requests.get(f"{BASE_URL}/api/v1/abhbp/search?q=burns")
print(f"Status: {r.status_code}")
print(f"Results: {r.json()['count']}")
print(f"Sample: {r.json()['results'][0] if r.json()['results'] else 'None'}\n")

# Test 2: Get by code
print("2️⃣ Get package BM001:")
r = requests.get(f"{BASE_URL}/api/v1/abhbp/BM001")
print(f"Status: {r.status_code}")
print(f"Data: {r.json()}\n")

# Test 3: List specialties
print("3️⃣ List specialties:")
r = requests.get(f"{BASE_URL}/api/v1/abhbp/specialties/list")
print(f"Status: {r.status_code}")
print(f"Specialties: {r.json()['specialties'][:5]}...")

print("\n✅ All tests passed!")
