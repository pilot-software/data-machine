#!/usr/bin/env python3
"""Download Ayushman Bharat HBP Package Master Data"""

import requests
import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

ABHBP_URL = "https://ayushmanbharat.mp.gov.in/uploads/media/HBP_2022_Package_Master1.xlsx"

def download_abhbp():
    print("📥 Downloading AB-HBP Package Master...")
    
    response = requests.get(ABHBP_URL, timeout=30)
    response.raise_for_status()
    
    excel_path = DATA_DIR / "abhbp_packages.xlsx"
    excel_path.write_bytes(response.content)
    
    print(f"✅ Downloaded: {excel_path}")
    
    # Read Excel with proper header row (skip first row)
    df = pd.read_excel(excel_path, header=1)
    
    # Clean and standardize column names
    df.columns = df.columns.str.strip().str.replace('\n', ' ')
    
    # Keep only essential columns
    cols_map = {
        'Specialty': 'specialty',
        'Package Code HBP 2022': 'package_code',
        'AB PM-JAY  Package Name': 'package_name',
        'AB PM-JAY  Procedure Name': 'procedure_name',
        'Procedure Price': 'base_rate'
    }
    
    # Select and rename columns
    available_cols = {k: v for k, v in cols_map.items() if k in df.columns}
    df = df[list(available_cols.keys())].rename(columns=available_cols)
    
    # Clean data
    df = df.dropna(subset=['package_code', 'package_name'])
    df['base_rate'] = pd.to_numeric(df['base_rate'], errors='coerce')
    
    csv_path = DATA_DIR / "abhbp_packages.csv"
    df.to_csv(csv_path, index=False)
    
    print(f"✅ Converted to CSV: {csv_path}")
    print(f"📊 Total packages: {len(df)}")
    print(f"📋 Columns: {list(df.columns)}")
    print(f"📝 Sample: {df.head(2).to_dict('records')}")
    
    return csv_path

if __name__ == "__main__":
    download_abhbp()
