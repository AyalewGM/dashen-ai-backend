#!/usr/bin/env python3
"""
Initialize Gasha Database
Creates all tables and sets up initial schema
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import init_db, engine
from app.modules.fraudshield.db_models import Base
from sqlalchemy import inspect

def check_database_exists():
    """Check if database tables already exist"""
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    return len(tables) > 0

def main():
    print("=" * 60)
    print("🛡️  Gasha Fraud Detection - Database Initialization")
    print("=" * 60)
    print()
    
    # Check if tables exist
    if check_database_exists():
        print("⚠️  Warning: Database tables already exist!")
        response = input("Do you want to drop and recreate all tables? (yes/no): ")
        if response.lower() != 'yes':
            print("❌ Aborted. No changes made.")
            return
        
        print("\n🗑️  Dropping all existing tables...")
        Base.metadata.drop_all(bind=engine)
        print("✅ All tables dropped")
    
    print("\n📊 Creating database tables...")
    print()
    
    # Create all tables
    init_db()
    
    print()
    print("=" * 60)
    print("✅ Database initialized successfully!")
    print("=" * 60)
    print()
    print("📋 Created tables:")
    print("   • transactions - Main transaction records")
    print("   • alerts - Fraud alerts")
    print("   • cases - Investigation cases")
    print("   • case_notes - Case investigation notes")
    print("   • fraud_patterns - Detected fraud patterns")
    print("   • audit_logs - Audit trail (10-year retention)")
    print("   • customer_profiles - Customer risk profiles")
    print()
    print("🚀 Ready to start fraud detection!")
    print()

if __name__ == "__main__":
    main()
