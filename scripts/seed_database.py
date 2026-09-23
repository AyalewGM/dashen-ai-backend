#!/usr/bin/env python3
"""
Database Seeding Script for Goozam AI Platform

Seeds the database with:
- Sample customers for each bank
- Sample accounts
- Sample transactions
- Sample KPIs
"""

import os
import sys
import random
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.modules.shared.db import get_db_conn, ensure_tables_exist
from app.modules.shared.bank_config import BANK_CONFIGS
from app.modules.shared.logging import logger


# Sample data
ETHIOPIAN_NAMES = [
    "Abebe Bikila", "Almaz Ayana", "Derartu Tulu", "Haile Gebrselassie",
    "Kenenisa Bekele", "Meseret Defar", "Tirunesh Dibaba", "Yonas Kinde",
    "Tsegaye Kebede", "Lelisa Desisa", "Feyisa Lilesa", "Tiki Gelana",
    "Mare Dibaba", "Aselefech Mergia", "Mestawot Tadesse", "Birhanu Legese",
    "Tamirat Tola", "Mosinet Geremew", "Shura Kitata", "Sisay Lemma"
]

ACCOUNT_TYPES = ["savings", "checking", "business", "investment"]
CHANNELS = ["mobile", "atm", "pos", "online", "branch", "agent"]
CATEGORIES = ["groceries", "utilities", "transport", "entertainment", "healthcare", "education", "shopping", "dining"]
ETHIOPIAN_CITIES = ["Addis Ababa", "Dire Dawa", "Mekelle", "Gondar", "Bahir Dar", "Hawassa", "Jimma", "Adama"]


def seed_customers(bank_id: str, count: int = 50):
    """Seed sample customers for a bank"""
    logger.info(f"🏦 Seeding {count} customers for {bank_id}...")
    
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            for i in range(count):
                customer_id = f"{bank_id}_cust_{i+1:04d}"
                name = random.choice(ETHIOPIAN_NAMES)
                email = f"{name.lower().replace(' ', '.')}@example.com"
                phone = f"+251{random.randint(900000000, 999999999)}"
                account_type = random.choice(ACCOUNT_TYPES)
                risk_score = random.randint(0, 100)
                
                cur.execute("""
                    INSERT INTO customers (customer_id, bank_id, name, email, phone, account_type, risk_score)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (customer_id) DO NOTHING
                """, (customer_id, bank_id, name, email, phone, account_type, risk_score))
            
            conn.commit()
    
    logger.info(f"✅ Seeded {count} customers for {bank_id}")


def seed_accounts(bank_id: str, customer_count: int = 50):
    """Seed sample accounts for customers"""
    logger.info(f"💰 Seeding accounts for {bank_id}...")
    
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            for i in range(customer_count):
                customer_id = f"{bank_id}_cust_{i+1:04d}"
                
                # Each customer gets 1-3 accounts
                num_accounts = random.randint(1, 3)
                for j in range(num_accounts):
                    account_id = f"{bank_id}_acc_{i+1:04d}_{j+1}"
                    account_type = random.choice(ACCOUNT_TYPES)
                    balance = Decimal(random.uniform(1000, 500000))
                    currency = BANK_CONFIGS[bank_id].currency
                    
                    cur.execute("""
                        INSERT INTO accounts (account_id, customer_id, bank_id, account_type, balance, currency, status)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (account_id) DO NOTHING
                    """, (account_id, customer_id, bank_id, account_type, balance, currency, 'active'))
            
            conn.commit()
    
    logger.info(f"✅ Seeded accounts for {bank_id}")


def seed_transactions(bank_id: str, customer_count: int = 50, tx_per_customer: int = 20):
    """Seed sample transactions"""
    logger.info(f"💳 Seeding transactions for {bank_id}...")
    
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            total_tx = 0
            
            for i in range(customer_count):
                customer_id = f"{bank_id}_cust_{i+1:04d}"
                
                # Get customer's accounts
                cur.execute("SELECT account_id FROM accounts WHERE customer_id = %s", (customer_id,))
                accounts = [row[0] for row in cur.fetchall()]
                
                if not accounts:
                    continue
                
                # Generate transactions for last 90 days
                for j in range(tx_per_customer):
                    tx_id = f"{bank_id}_tx_{i+1:04d}_{j+1:04d}"
                    account_id = random.choice(accounts)
                    
                    # Random timestamp in last 90 days
                    days_ago = random.randint(0, 90)
                    tx_timestamp = datetime.now() - timedelta(days=days_ago, hours=random.randint(0, 23), minutes=random.randint(0, 59))
                    
                    amount = Decimal(random.uniform(10, 50000))
                    currency = BANK_CONFIGS[bank_id].currency
                    direction = random.choice(['debit', 'credit'])
                    channel = random.choice(CHANNELS)
                    category = random.choice(CATEGORIES)
                    location_city = random.choice(ETHIOPIAN_CITIES)
                    
                    cur.execute("""
                        INSERT INTO transactions (
                            tx_id, customer_id, account_id, bank_id, tx_timestamp, 
                            amount, currency, direction, channel, category, 
                            location_city, location_country
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (tx_id) DO NOTHING
                    """, (
                        tx_id, customer_id, account_id, bank_id, tx_timestamp,
                        amount, currency, direction, channel, category,
                        location_city, 'Ethiopia'
                    ))
                    
                    total_tx += 1
            
            conn.commit()
    
    logger.info(f"✅ Seeded {total_tx} transactions for {bank_id}")


def seed_kpis(bank_id: str, days: int = 90):
    """Seed sample KPIs for internal analytics"""
    logger.info(f"📊 Seeding KPIs for {bank_id}...")
    
    metrics = [
        "total_customers",
        "active_customers",
        "new_customers",
        "total_deposits",
        "total_loans",
        "transaction_volume",
        "transaction_count",
        "mobile_banking_users",
        "atm_transactions",
        "branch_visits"
    ]
    
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            total_kpis = 0
            
            for day_offset in range(days):
                kpi_date = (datetime.now() - timedelta(days=day_offset)).date()
                
                for metric in metrics:
                    # Generate realistic values
                    if metric == "total_customers":
                        value = Decimal(random.randint(10000, 50000))
                    elif metric == "active_customers":
                        value = Decimal(random.randint(5000, 30000))
                    elif metric == "new_customers":
                        value = Decimal(random.randint(10, 200))
                    elif metric in ["total_deposits", "total_loans"]:
                        value = Decimal(random.uniform(1000000, 10000000))
                    elif metric == "transaction_volume":
                        value = Decimal(random.uniform(500000, 5000000))
                    elif metric == "transaction_count":
                        value = Decimal(random.randint(1000, 10000))
                    else:
                        value = Decimal(random.randint(100, 5000))
                    
                    cur.execute("""
                        INSERT INTO internal_kpis (bank_id, kpi_date, metric_name, metric_value)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (bank_id, kpi_date, metric_name, segment_type, segment_value) DO NOTHING
                    """, (bank_id, kpi_date, metric, value))
                    
                    total_kpis += 1
            
            conn.commit()
    
    logger.info(f"✅ Seeded {total_kpis} KPIs for {bank_id}")


def seed_bank(bank_id: str):
    """Seed all data for a specific bank"""
    logger.info(f"")
    logger.info(f"{'='*60}")
    logger.info(f"🏦 SEEDING DATA FOR: {BANK_CONFIGS[bank_id].bank_name}")
    logger.info(f"{'='*60}")
    
    seed_customers(bank_id, count=50)
    seed_accounts(bank_id, customer_count=50)
    seed_transactions(bank_id, customer_count=50, tx_per_customer=20)
    seed_kpis(bank_id, days=90)
    
    logger.info(f"✅ Completed seeding for {BANK_CONFIGS[bank_id].bank_name}")


def seed_all_banks():
    """Seed data for all banks"""
    logger.info("🚀 Starting database seeding for all banks...")
    logger.info("")
    
    # Ensure tables exist first
    ensure_tables_exist()
    
    # Seed each bank
    for bank_id in BANK_CONFIGS.keys():
        seed_bank(bank_id)
    
    logger.info("")
    logger.info("="*60)
    logger.info("🎉 DATABASE SEEDING COMPLETE!")
    logger.info("="*60)
    logger.info("")
    logger.info("📊 Summary:")
    logger.info(f"   Banks seeded: {len(BANK_CONFIGS)}")
    logger.info(f"   Customers per bank: 50")
    logger.info(f"   Accounts per bank: ~100")
    logger.info(f"   Transactions per bank: ~1000")
    logger.info(f"   KPIs per bank: ~900")
    logger.info("")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Seed database with sample data")
    parser.add_argument(
        "--bank",
        type=str,
        help="Seed specific bank only (e.g., dashen, tsehay, cbe)",
        choices=list(BANK_CONFIGS.keys())
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear existing data before seeding"
    )
    
    args = parser.parse_args()
    
    # Clear data if requested
    if args.clear:
        logger.warning("🗑️  Clearing existing data...")
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("TRUNCATE TABLE transactions CASCADE")
                cur.execute("TRUNCATE TABLE accounts CASCADE")
                cur.execute("TRUNCATE TABLE customers CASCADE")
                cur.execute("TRUNCATE TABLE internal_kpis CASCADE")
            conn.commit()
        logger.info("✅ Data cleared")
    
    # Seed specific bank or all banks
    if args.bank:
        ensure_tables_exist()
        seed_bank(args.bank)
    else:
        seed_all_banks()


if __name__ == "__main__":
    main()
