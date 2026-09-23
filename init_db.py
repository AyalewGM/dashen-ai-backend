#!/usr/bin/env python3
"""
Initialize Gasha Database
Run this to create all database tables
"""

from app.database import init_db

if __name__ == "__main__":
    print("=" * 60)
    print("🛡️  Gasha Fraud Detection - Database Initialization")
    print("=" * 60)
    print()
    print("📊 Creating database tables...")
    
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
