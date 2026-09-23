#!/usr/bin/env python3
"""
Complete Database Setup Script
Creates all tables and seeds data for analytics and fraud monitoring
"""

import os
import random
import sys
import uuid
from datetime import datetime, timedelta
from decimal import Decimal

import psycopg2
from psycopg2.extensions import connection as PgConnection
from psycopg2.extras import execute_values


def get_db_connection() -> PgConnection:
    """Get database connection."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ ERROR: DATABASE_URL environment variable not set")
        print("\nSet it like this:")
        print("export DATABASE_URL='postgresql://user:password@localhost:5432/dbname'")
        sys.exit(1)
    
    try:
        conn = psycopg2.connect(database_url)
        print(f"✅ Connected to database")
        return conn
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        sys.exit(1)


def create_tables(conn: PgConnection):
    """Create all necessary tables."""
    print("\n📋 Creating tables...")
    
    ddl_statements = [
        # Customers table
        """
        CREATE TABLE IF NOT EXISTS customers (
            customer_id TEXT PRIMARY KEY,
            bank_id TEXT NOT NULL DEFAULT 'dashen',
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            account_type TEXT NOT NULL,
            risk_score INTEGER DEFAULT 0,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """,
        
        # Accounts table
        """
        CREATE TABLE IF NOT EXISTS accounts (
            account_id TEXT PRIMARY KEY,
            customer_id TEXT NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
            bank_id TEXT NOT NULL DEFAULT 'dashen',
            account_type TEXT NOT NULL,
            balance NUMERIC NOT NULL DEFAULT 0,
            currency TEXT NOT NULL DEFAULT 'ETB',
            status TEXT NOT NULL DEFAULT 'active',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """,
        
        # Transactions table
        """
        CREATE TABLE IF NOT EXISTS transactions (
            tx_id TEXT PRIMARY KEY,
            customer_id TEXT NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
            account_id TEXT REFERENCES accounts(account_id) ON DELETE SET NULL,
            bank_id TEXT NOT NULL DEFAULT 'dashen',
            tx_timestamp TIMESTAMPTZ NOT NULL,
            amount NUMERIC NOT NULL,
            currency TEXT NOT NULL DEFAULT 'ETB',
            direction TEXT NOT NULL CHECK (direction IN ('debit','credit')),
            channel TEXT NOT NULL,
            merchant TEXT,
            category TEXT,
            subcategory TEXT,
            location_country TEXT,
            location_city TEXT,
            region TEXT,
            branch TEXT,
            device_id TEXT,
            ip_address TEXT,
            reference_text TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """,
        
        # Fraud events table
        """
        CREATE TABLE IF NOT EXISTS fraud_events (
            event_id TEXT PRIMARY KEY,
            tx_id TEXT REFERENCES transactions(tx_id) ON DELETE SET NULL,
            customer_id TEXT NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
            bank_id TEXT NOT NULL DEFAULT 'dashen',
            event_timestamp TIMESTAMPTZ NOT NULL,
            amount NUMERIC NOT NULL,
            currency TEXT NOT NULL DEFAULT 'ETB',
            channel TEXT NOT NULL,
            event_type TEXT NOT NULL,
            risk_score INTEGER NOT NULL,
            risk_level TEXT NOT NULL CHECK (risk_level IN ('low','medium','high')),
            fraud_reasons TEXT[],
            is_confirmed_fraud BOOLEAN DEFAULT FALSE,
            reviewed_by TEXT,
            reviewed_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """,
        
        # Internal KPIs table
        """
        CREATE TABLE IF NOT EXISTS internal_kpis (
            kpi_id SERIAL PRIMARY KEY,
            bank_id TEXT NOT NULL DEFAULT 'dashen',
            kpi_date DATE NOT NULL,
            metric_name TEXT NOT NULL,
            metric_value NUMERIC NOT NULL,
            segment_type TEXT,
            segment_value TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE(bank_id, kpi_date, metric_name, segment_type, segment_value)
        );
        """,
        
        # Banking intelligence metrics table
        """
        CREATE TABLE IF NOT EXISTS intelligence_metrics (
            metric_id SERIAL PRIMARY KEY,
            bank_id TEXT NOT NULL DEFAULT 'dashen',
            metric_date DATE NOT NULL,
            metric_type TEXT NOT NULL,
            metric_name TEXT NOT NULL,
            metric_value NUMERIC NOT NULL,
            metadata JSONB,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """,
        
        # Fraud patterns table
        """
        CREATE TABLE IF NOT EXISTS fraud_patterns (
            pattern_id TEXT PRIMARY KEY,
            bank_id TEXT NOT NULL DEFAULT 'dashen',
            pattern_type TEXT NOT NULL,
            pattern_name TEXT NOT NULL,
            description TEXT,
            detection_count INTEGER DEFAULT 0,
            severity TEXT NOT NULL CHECK (severity IN ('low','medium','high','critical')),
            first_detected TIMESTAMPTZ NOT NULL,
            last_detected TIMESTAMPTZ NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """,
        
        # Datasets table (for file uploads)
        """
        CREATE TABLE IF NOT EXISTS datasets (
            dataset_id UUID PRIMARY KEY,
            dataset_name TEXT NOT NULL,
            dataset_type TEXT NOT NULL CHECK (dataset_type IN ('customer','internal')),
            uploaded_by_actor_type TEXT NOT NULL CHECK (uploaded_by_actor_type IN ('internal','customer')),
            uploaded_by_actor_id TEXT NOT NULL,
            file_path TEXT NOT NULL,
            row_count INTEGER NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """,
        
        # Indexes
        "CREATE INDEX IF NOT EXISTS idx_transactions_customer_time ON transactions(customer_id, tx_timestamp);",
        "CREATE INDEX IF NOT EXISTS idx_transactions_bank_time ON transactions(bank_id, tx_timestamp);",
        "CREATE INDEX IF NOT EXISTS idx_fraud_events_customer ON fraud_events(customer_id, event_timestamp);",
        "CREATE INDEX IF NOT EXISTS idx_fraud_events_bank ON fraud_events(bank_id, event_timestamp);",
        "CREATE INDEX IF NOT EXISTS idx_internal_kpis_metric_date ON internal_kpis(bank_id, metric_name, kpi_date);",
        "CREATE INDEX IF NOT EXISTS idx_intelligence_metrics_bank_date ON intelligence_metrics(bank_id, metric_date);",
    ]
    
    with conn.cursor() as cur:
        for i, stmt in enumerate(ddl_statements, 1):
            try:
                cur.execute(stmt)
                print(f"  ✓ Statement {i}/{len(ddl_statements)}")
            except Exception as e:
                print(f"  ✗ Failed statement {i}: {e}")
                raise
    
    conn.commit()
    print("✅ All tables created successfully")


def seed_customers(conn: PgConnection, bank_id: str = "dashen", count: int = 100):
    """Seed customer data."""
    print(f"\n👥 Seeding {count} customers for {bank_id}...")

    account_types = ["savings", "checking", "business", "premium"]

    ethiopian_names = [
        "Abebe Kebede", "Aster Aweke", "Tilahun Gessesse", "Mulatu Astatke",
        "Haile Gebrselassie", "Kenenisa Bekele", "Almaz Ayana", "Tirunesh Dibaba",
        "Derartu Tulu", "Meseret Defar", "Mahmoud Ahmed", "Ali Birra",
        "Ejigayehu Shibabaw", "Teddy Afro", "Eyob Mekonnen", "Bethlehem Tilahun",
        "Eleni Gabre-Madhin", "Dawit Kebede", "Frehiwot Tadesse", "Yonas Alemu",
        "Selamawit Berhe", "Kassahun Assefa", "Genet Mekonnen", "Chala Begashaw",
        "Hiwot Girma", "Bekalu Tadesse", "Mekdes Demeke", "Fikru Hailu",
        "Netsanet Girma", "Robel Alemayehu", "Saba Tewodros", "Lemma Tadesse",
        "Werknesh Mergia", "Paulos Kidane", "Tigist Haile", "Obsa Gutema",
        "Gelila Bekele", "Jemal Yusuf", "Zerihun Assefa", "Maheder Alebel",
        "Desta Begashaw", "Yared Negu", "Seifu Fantahun", "Tewodros Kassahun",
        "Abeba Hailu", "Mikiyas Chernet", "Tiruwork Tadesse", "Addisu Bekele",
        "Lemlem Aregawi", "Qenean Gebre",
    ]

    customers = []
    for i in range(1, count + 1):
        customer_id = f"{bank_id}-cust-{i:04d}"
        name = random.choice(ethiopian_names)
        email_slug = name.lower().replace(" ", ".").replace("-", "")
        email = f"{email_slug}{i}@{bank_id}bank.com"
        phone = f"+251-9{random.randint(10000000, 99999999)}"
        account_type = random.choice(account_types)
        risk_score = random.randint(0, 100)

        customers.append((customer_id, bank_id, name, email, phone, account_type, risk_score))
    
    with conn.cursor() as cur:
        execute_values(
            cur,
            """
            INSERT INTO customers (customer_id, bank_id, name, email, phone, account_type, risk_score)
            VALUES %s
            ON CONFLICT (customer_id) DO NOTHING
            """,
            customers,
            page_size=10000,
        )
    
    conn.commit()
    print(f"✅ Seeded {len(customers)} customers")


def seed_accounts(conn: PgConnection, bank_id: str = "dashen"):
    """Seed account data."""
    print(f"\n💳 Seeding accounts for {bank_id}...")
    
    # Get customers
    with conn.cursor() as cur:
        cur.execute("SELECT customer_id FROM customers WHERE bank_id = %s", (bank_id,))
        customer_ids = [row[0] for row in cur.fetchall()]
    
    accounts = []
    for customer_id in customer_ids:
        # Each customer gets 1-3 accounts
        num_accounts = random.randint(1, 3)
        for j in range(num_accounts):
            account_id = f"{customer_id}-acc-{j+1}"
            account_type = random.choice(["savings", "checking", "business"])
            balance = Decimal(random.uniform(1000, 500000))
            
            accounts.append((account_id, customer_id, bank_id, account_type, balance))
    
    with conn.cursor() as cur:
        execute_values(
            cur,
            """
            INSERT INTO accounts (account_id, customer_id, bank_id, account_type, balance)
            VALUES %s
            ON CONFLICT (account_id) DO NOTHING
            """,
            accounts,
            page_size=10000,
        )
    
    conn.commit()
    print(f"✅ Seeded {len(accounts)} accounts")


def seed_transactions(conn: PgConnection, bank_id: str = "dashen", days: int = 90):
    """Seed transaction data."""
    print(f"\n💸 Seeding transactions for {bank_id} ({days} days)...")
    
    # Get accounts
    with conn.cursor() as cur:
        cur.execute("""
            SELECT a.account_id, a.customer_id 
            FROM accounts a 
            JOIN customers c ON a.customer_id = c.customer_id 
            WHERE c.bank_id = %s
        """, (bank_id,))
        accounts = cur.fetchall()
    
    channels = ["atm", "mobile", "web", "branch", "pos"]
    categories = ["transfer", "payment", "withdrawal", "deposit", "purchase"]
    merchants = ["Shoa Supermarket", "Abyssinia Restaurant", "Merkato Traders", "Bole Electronics", "AwashFuel"]
    cities = ["Addis Ababa", "Adama", "Bahir Dar", "Mekelle", "Hawassa", "Dire Dawa", "Jimma", "Gondar", "Bishoftu", "Dessie"]
    regions = ["Addis Ababa", "Oromia", "Amhara", "Tigray", "SNNPR", "Sidama", "Afar", "Somali", "Harari"]
    branches = ["Main Branch", "Bole", "Megenagna", "Piyassa", "Sarbet", "Arat Kilo", "CMC", "Gotera", "Wollo Sefer", "Merkato", "Lideta"]
    
    transactions = []
    end_date = datetime.now()
    
    for account_id, customer_id in accounts:
        # Each account gets 5-20 transactions
        num_txs = random.randint(5, 20)
        
        for _ in range(num_txs):
            tx_id = f"tx-{bank_id}-{uuid.uuid4().hex[:12]}"
            tx_timestamp = end_date - timedelta(days=random.randint(0, days))
            amount = Decimal(random.uniform(100, 50000))
            direction = random.choice(["debit", "credit"])
            channel = random.choice(channels)
            merchant = random.choice(merchants) if channel in ["pos", "web"] else None
            category = random.choice(categories)
            location_city = random.choice(cities)
            region = random.choice(regions)
            branch = random.choice(branches)
            device_id = f"dev-{random.randint(1000, 9999)}"
            ip_address = f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}"

            transactions.append((
                tx_id, customer_id, account_id, bank_id, tx_timestamp, amount,
                direction, channel, merchant, category, location_city, region, branch,
                device_id, ip_address
            ))
    
    with conn.cursor() as cur:
        execute_values(
            cur,
            """
            INSERT INTO transactions (
                tx_id, customer_id, account_id, bank_id, tx_timestamp, amount,
                direction, channel, merchant, category, location_city, region, branch,
                device_id, ip_address
            )
            VALUES %s
            ON CONFLICT (tx_id) DO NOTHING
            """,
            transactions,
            page_size=10000,
        )
    
    conn.commit()
    print(f"✅ Seeded {len(transactions)} transactions")


def seed_fraud_events(conn: PgConnection, bank_id: str = "dashen"):
    """Seed fraud event data."""
    print(f"\n🚨 Seeding fraud events for {bank_id}...")
    
    # Get some transactions
    with conn.cursor() as cur:
        cur.execute("""
            SELECT tx_id, customer_id, tx_timestamp, amount, channel 
            FROM transactions 
            WHERE bank_id = %s 
            ORDER BY RANDOM() 
            LIMIT 50
        """, (bank_id,))
        transactions = cur.fetchall()
    
    fraud_reasons_options = [
        ["unusually_large_amount"],
        ["suspicious_channel_mix"],
        ["new_device"],
        ["unusual_hours"],
        ["rapid_transaction_velocity"],
        ["unusually_large_amount", "suspicious_channel_mix"],
        ["new_device", "unusual_hours"],
    ]
    
    fraud_events = []
    for tx_id, customer_id, tx_timestamp, amount, channel in transactions:
        event_id = f"fraud-{bank_id}-{uuid.uuid4().hex[:12]}"
        risk_score = random.randint(30, 95)
        
        if risk_score >= 70:
            risk_level = "high"
        elif risk_score >= 45:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        fraud_reasons = random.choice(fraud_reasons_options)
        is_confirmed = random.random() < 0.1  # 10% confirmed fraud
        
        fraud_events.append((
            event_id, tx_id, customer_id, bank_id, tx_timestamp, amount,
            channel, "transaction", risk_score, risk_level, fraud_reasons, is_confirmed
        ))
    
    with conn.cursor() as cur:
        execute_values(
            cur,
            """
            INSERT INTO fraud_events (
                event_id, tx_id, customer_id, bank_id, event_timestamp, amount,
                channel, event_type, risk_score, risk_level, fraud_reasons, is_confirmed_fraud
            )
            VALUES %s
            ON CONFLICT (event_id) DO NOTHING
            """,
            fraud_events,
            page_size=5000,
        )
    
    conn.commit()
    print(f"✅ Seeded {len(fraud_events)} fraud events")


def seed_internal_kpis(conn: PgConnection, bank_id: str = "dashen", days: int = 90):
    """Seed internal KPI data."""
    print(f"\n📊 Seeding internal KPIs for {bank_id} ({days} days)...")
    
    metrics = [
        "deposits", "loans", "npl_proxy", "digital_adoption",
        "customer_count", "transaction_volume", "revenue",
        "cost_to_income_ratio", "customer_satisfaction"
    ]
    
    kpis = []
    end_date = datetime.now().date()
    
    for day_offset in range(days):
        kpi_date = end_date - timedelta(days=day_offset)
        
        for metric in metrics:
            # Generate realistic values with some growth
            base_value = {
                "deposits": 45_000_000_000 + (day_offset * 100_000_000),
                "loans": 32_000_000_000 + (day_offset * 80_000_000),
                "npl_proxy": 2.1 + random.uniform(-0.1, 0.1),
                "digital_adoption": 0.62 + (day_offset * 0.001),
                "customer_count": 1_200_000 + (day_offset * 500),
                "transaction_volume": 50_000 + random.randint(-5000, 5000),
                "revenue": 2_500_000 + random.randint(-100000, 100000),
                "cost_to_income_ratio": 45.5 + random.uniform(-2, 2),
                "customer_satisfaction": 4.2 + random.uniform(-0.2, 0.2),
            }
            
            value = Decimal(str(base_value.get(metric, 0)))
            kpis.append((bank_id, kpi_date, metric, value))
    
    with conn.cursor() as cur:
        execute_values(
            cur,
            """
            INSERT INTO internal_kpis (bank_id, kpi_date, metric_name, metric_value)
            VALUES %s
            ON CONFLICT (bank_id, kpi_date, metric_name, segment_type, segment_value) DO NOTHING
            """,
            kpis,
            page_size=10000,
        )
    
    conn.commit()
    print(f"✅ Seeded {len(kpis)} KPI records")


def seed_fraud_patterns(conn: PgConnection, bank_id: str = "dashen"):
    """Seed fraud pattern data."""
    print(f"\n🔍 Seeding fraud patterns for {bank_id}...")
    
    patterns = [
        ("pat-velocity-burst", "velocity_burst", "Rapid Transaction Velocity", 
         "Multiple transactions in short time window", "high"),
        ("pat-channel-conc", "channel_concentration", "Channel Concentration",
         "Unusual concentration of transactions on single channel", "medium"),
        ("pat-time-anomaly", "unusual_time_pattern", "Unusual Time Pattern",
         "Transactions during unusual hours (12am-6am)", "medium"),
        ("pat-amount-struct", "amount_structuring", "Amount Structuring",
         "Transactions just below reporting threshold", "high"),
        ("pat-geo-anomaly", "geographic_anomaly", "Geographic Anomaly",
         "Transactions from unusual locations", "medium"),
    ]
    
    pattern_data = []
    now = datetime.now()
    
    for pattern_id, pattern_type, pattern_name, description, severity in patterns:
        full_pattern_id = f"{bank_id}-{pattern_id}"
        detection_count = random.randint(5, 50)
        first_detected = now - timedelta(days=random.randint(30, 90))
        last_detected = now - timedelta(days=random.randint(0, 7))
        
        pattern_data.append((
            full_pattern_id, bank_id, pattern_type, pattern_name, description,
            detection_count, severity, first_detected, last_detected
        ))
    
    with conn.cursor() as cur:
        execute_values(
            cur,
            """
            INSERT INTO fraud_patterns (
                pattern_id, bank_id, pattern_type, pattern_name, description,
                detection_count, severity, first_detected, last_detected
            )
            VALUES %s
            ON CONFLICT (pattern_id) DO NOTHING
            """,
            pattern_data,
            page_size=1000,
        )
    
    conn.commit()
    print(f"✅ Seeded {len(pattern_data)} fraud patterns")


def main():
    """Main setup function."""
    print("=" * 60)
    print("🚀 FraudShield Database Setup")
    print("=" * 60)

    # Scale the seed from the environment
    customers_per_bank = int(os.getenv("CUSTOMERS_PER_BANK", "50"))
    days = int(os.getenv("SEED_DAYS", "90"))
    print(f"🔧 Scale: {customers_per_bank} customers per bank, {days} days of history")

    # Get connection
    conn = get_db_connection()

    try:
        # Create tables
        create_tables(conn)

        # Seed data for all 8 banks
        banks = ["dashen", "abyssinia", "awash", "cbe", "amhara", "zemen", "tsedey", "nib"]

        for bank_id in banks:
            print(f"\n{'=' * 60}")
            print(f"🏦 Seeding data for {bank_id.upper()} Bank")
            print(f"{'=' * 60}")

            seed_customers(conn, bank_id, count=customers_per_bank)
            seed_accounts(conn, bank_id)
            seed_transactions(conn, bank_id, days=days)
            seed_fraud_events(conn, bank_id)
            seed_internal_kpis(conn, bank_id, days=days)
            seed_fraud_patterns(conn, bank_id)
        
        print(f"\n{'=' * 60}")
        print("✅ Database setup complete!")
        print(f"{'=' * 60}")
        print("\n📊 Summary:")
        
        # Get counts
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM customers")
            customer_count = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM accounts")
            account_count = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM transactions")
            tx_count = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM fraud_events")
            fraud_count = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM internal_kpis")
            kpi_count = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM fraud_patterns")
            pattern_count = cur.fetchone()[0]
        
        print(f"  • Customers: {customer_count:,}")
        print(f"  • Accounts: {account_count:,}")
        print(f"  • Transactions: {tx_count:,}")
        print(f"  • Fraud Events: {fraud_count:,}")
        print(f"  • KPI Records: {kpi_count:,}")
        print(f"  • Fraud Patterns: {pattern_count:,}")
        
        print("\n🎉 Ready to use!")
        
    except Exception as e:
        print(f"\n❌ Error during setup: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
