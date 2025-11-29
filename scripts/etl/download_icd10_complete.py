#!/usr/bin/env python3
"""Download ICD-10 codes from WHO API with authentication"""
import requests
import psycopg2
import time

DB_URL = "postgresql://samirkolhe@localhost:5432/hms_terminology"
CLIENT_ID = "f027b85b-e451-4a03-871a-d5e96778ffc1_9056b59a-973c-4e09-9190-e1a18a88f68b"
CLIENT_SECRET = "hTgKi4F3Nh2kfNRt29xlGOIlkXv60pQBosynSy34LWM="
TOKEN_URL = "https://icdaccessmanagement.who.int/connect/token"
API_URL = "https://id.who.int/icd/release/10/2019"

def get_token():
    """Get OAuth token from WHO"""
    payload = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'scope': 'icdapi_access',
        'grant_type': 'client_credentials'
    }
    response = requests.post(TOKEN_URL, data=payload)
    return response.json()['access_token']

def fetch_entity(url, token, depth=0):
    """Recursively fetch ICD-10 entities"""
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/json',
        'Accept-Language': 'en',
        'API-Version': 'v2'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"Error {response.status_code}: {url}")
            return []
        
        data = response.json()
        if depth == 0:
            print(f"Response keys: {list(data.keys())[:5]}")
        entities = []
        
        code = data.get('code', '').replace('.', '').replace('-', '')
        title = data.get('title', {})
        if isinstance(title, dict):
            title = title.get('@value', '')
        
        if code and title:
            entities.append({'code': code, 'term': title, 'chapter': title[:50]})
            print(f"{'  ' * depth}{code}: {title[:60]}")
        
        if depth < 3 and 'child' in data:
            for child_url in data['child']:
                time.sleep(0.1)
                entities.extend(fetch_entity(child_url, token, depth + 1))
        
        return entities
    except Exception as e:
        print(f"Exception: {e}")
        return []

def fetch_who_codes(token):
    """Fetch all ICD-10 codes from WHO"""
    all_codes = []
    
    # Get root entity first
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/json',
        'Accept-Language': 'en',
        'API-Version': 'v2'
    }
    
    # Fetch chapters from root
    try:
        print(f"Fetching root: {API_URL}")
        response = requests.get(API_URL, headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Keys in response: {list(data.keys())}")
            if 'child' in data:
                print(f"Found {len(data['child'])} chapters")
                for child_url in data['child'][:10]:  # Limit to first 10 chapters
                    print(f"\n📚 Fetching {child_url.split('/')[-1]}...")
                    codes = fetch_entity(child_url, token, depth=0)
                    all_codes.extend(codes)
                    time.sleep(0.5)
            else:
                print("No 'child' key in response")
        else:
            print(f"Error response: {response.text[:200]}")
    except Exception as e:
        print(f"Error fetching root: {e}")
        import traceback
        traceback.print_exc()
    
    return all_codes

def download_icd10_complete():
    """Download ICD-10 codes from WHO"""
    print("🔑 Getting WHO API token...")
    try:
        token = get_token()
        print("✅ Token obtained")
    except Exception as e:
        print(f"⚠️  Token failed: {e}")
        print("⏭️  Skipping WHO API download")
        return
    
    print("\n📥 Fetching ICD-10 codes from WHO API (timeout: 30s)...")
    import signal
    
    def timeout_handler(signum, frame):
        raise TimeoutError("API fetch timeout")
    
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(30)
    
    try:
        codes = fetch_who_codes(token)
        signal.alarm(0)
    except TimeoutError:
        print("⚠️  WHO API timeout - skipping")
        return
    except Exception as e:
        print(f"⚠️  WHO API error: {e}")
        return
    
    if not codes:
        print("⚠️  No codes fetched from WHO - skipping")
        return
    
    print(f"\n✅ Fetched {len(codes)} codes from WHO")
    
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    
    inserted = 0
    for code_data in codes:
        try:
            cur.execute(
                "INSERT INTO icd10_codes (code, term, chapter, active) VALUES (%s, %s, %s, true) ON CONFLICT (code) DO UPDATE SET term = EXCLUDED.term",
                (code_data['code'], code_data['term'], code_data['chapter'])
            )
            if cur.rowcount > 0:
                inserted += 1
        except Exception as e:
            pass
    
    conn.commit()
    cur.close()
    conn.close()
    
    print(f"✅ Inserted/Updated {inserted} codes")
    print(f"📊 Total from WHO API: {len(codes)} codes")

if __name__ == "__main__":
    download_icd10_complete()
