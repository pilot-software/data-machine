#!/usr/bin/env python3

import asyncio
import os
from init_db import init_database

async def setup_project():
    """Complete project setup"""
    
    print("🚀 Setting up HMS Terminology Service...")
    
    # Check environment file
    if not os.path.exists('.env'):
        print("⚠️  .env file not found, copying from .env.example")
        if os.path.exists('.env.example'):
            os.system('cp .env.example .env')
        else:
            print("❌ .env.example not found")
            return
    
    # Initialize database
    print("📊 Initializing database...")
    await init_database()
    
    print("✅ Setup complete!")
    print("\nNext steps:")
    print("1. Edit .env file with your database and Redis settings")
    print("2. Run: ./run.sh")
    print("3. Test: curl http://localhost:8001/api/v1/health")

if __name__ == "__main__":
    asyncio.run(setup_project())