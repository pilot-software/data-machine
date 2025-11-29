#!/usr/bin/env python3
"""Download ICD-10 codes from WHO API"""
import requests
import psycopg2
import time

DB_URL = "postgresql://samirkolhe@localhost:5432/hms_terminology"
WHO_API = "https://id.who.int/icd/release/10/2019"

def fetch_entity(url, depth=0):
    """Fetch ICD-10 entity recursively"""
    headers = {
        'Accept': 'application/json',
        'Accept-Language': 'en',
        'API-Version': 'v2'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return []
        
        data = response.json()
        entities = []
        
        code = data.get('code', '').replace('.', '').replace('-', '')
        title = data.get('title', {})
        if isinstance(title, dict):
            title = title.get('@value', '')
        
        if code and title:
            entities.append({'code': code, 'term': title, 'chapter': title[:50]})
            print(f"{'  ' * depth}{code}: {title[:60]}")
        
        if depth < 2 and 'child' in data:
            for child_url in data['child'][:50]:
                time.sleep(0.1)
                entities.extend(fetch_entity(child_url, depth + 1))
        
        return entities
    except Exception as e:
        print(f"Error: {e}")
        return []

def download_icd10_who():
    """Download ICD-10 from WHO"""
    print("📥 Downloading ICD-10 from WHO API...")
    
    chapters = [
        f"{WHO_API}/A00-B99",
        f"{WHO_API}/C00-D48",
        f"{WHO_API}/E00-E90",
        f"{WHO_API}/I00-I99",
        f"{WHO_API}/J00-J99",
        f"{WHO_API}/R00-R99"
    ]
    
    all_codes = []
    for chapter_url in chapters:
        print(f"\n📖 Fetching {chapter_url.split('/')[-1]}...")
        codes = fetch_entity(chapter_url)
        all_codes.extend(codes)
    
    print(f"\n✅ Fetched {len(all_codes)} codes")
    
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    
    inserted = 0
    for code_data in all_codes:
        try:
            cur.execute(
                "INSERT INTO icd10_codes (code, term, chapter, active) VALUES (%s, %s, %s, true) ON CONFLICT (code) DO NOTHING",
                (code_data['code'], code_data['term'], code_data['chapter'])
            )
            if cur.rowcount > 0:
                inserted += 1
        except Exception as e:
            pass
    
    conn.commit()
    cur.close()
    conn.close()
    
    print(f"✅ Inserted {inserted} new codes")

if __name__ == "__main__":
    download_icd10_who()
