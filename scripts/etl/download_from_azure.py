#!/usr/bin/env python3
"""Download ABHBP data from Azure Blob Storage"""
import os
from azure.storage.blob import BlobServiceClient

STORAGE_ACCOUNT = os.getenv("AZURE_STORAGE_ACCOUNT", "your-storage-account")
CONTAINER_NAME = os.getenv("AZURE_CONTAINER_NAME", "data-files")
BLOB_NAME = "abhbp_packages.xlsx"
LOCAL_PATH = "data/abhbp_packages.xlsx"

def download_from_azure():
    """Download file from Azure Blob Storage"""
    connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    
    if not connection_string:
        print("❌ AZURE_STORAGE_CONNECTION_STRING not set")
        return False
    
    try:
        blob_service = BlobServiceClient.from_connection_string(connection_string)
        blob_client = blob_service.get_blob_client(container=CONTAINER_NAME, blob=BLOB_NAME)
        
        os.makedirs("data", exist_ok=True)
        
        with open(LOCAL_PATH, "wb") as f:
            f.write(blob_client.download_blob().readall())
        
        print(f"✅ Downloaded {BLOB_NAME} to {LOCAL_PATH}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    download_from_azure()
