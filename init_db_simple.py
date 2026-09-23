#!/usr/bin/env python3
"""
Simple database initialization - creates tables in correct order
"""

from app.database import engine
from app.modules.fraudshield.db_models import (
    Transaction,
    CustomerProfile,
    Alert,
    Case,
    CaseNote,
    FraudPatternDetection,
    AuditLog,
)

print("=" * 60)
print("🛡️  Gasha - Simple Database Initialization")
print("=" * 60)
print()

# Create tables in correct order (respecting foreign keys)
tables_in_order = [
    ("transactions", Transaction.__table__),
    ("customer_profiles", CustomerProfile.__table__),
    ("cases", Case.__table__),
    ("alerts", Alert.__table__),
    ("case_notes", CaseNote.__table__),
    ("fraud_patterns", FraudPatternDetection.__table__),
    ("audit_logs", AuditLog.__table__),
]

for name, table in tables_in_order:
    print(f"Creating table: {name}...")
    try:
        table.create(engine, checkfirst=True)
        print(f"  ✅ {name} created")
    except Exception as e:
        print(f"  ❌ Error creating {name}: {e}")

print()
print("=" * 60)
print("✅ Database initialization complete!")
print("=" * 60)
