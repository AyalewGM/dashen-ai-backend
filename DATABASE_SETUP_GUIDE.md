# 🗄️ Database Setup Guide

## Complete Local Database Setup with Seed Data

This guide will help you set up a PostgreSQL database with all tables and seed data for **analytics** and **fraud monitoring**.

---

## 🚀 **Quick Start (Docker)**

### **Option 1: Using Docker Compose (Recommended)**

```bash
# 1. Start PostgreSQL + API
docker-compose up -d

# 2. Wait for database to be ready (about 10 seconds)
sleep 10

# 3. Run setup script
docker-compose exec fraudshield-api python setup_database.py

# Done! Database is ready with all seed data
```

---

### **Option 2: Local PostgreSQL**

```bash
# 1. Install PostgreSQL (if not already installed)
# macOS:
brew install postgresql@15
brew services start postgresql@15

# Ubuntu/Debian:
sudo apt-get install postgresql-15

# 2. Create database
createdb fraudshield_demo

# 3. Set environment variable
export DATABASE_URL="postgresql://localhost:5432/fraudshield_demo"

# 4. Run setup script
python3 setup_database.py

# Done!
```

---

## 📊 **What Gets Created**

### **Tables (9 Total)**

| Table | Purpose | Records Seeded |
|-------|---------|----------------|
| **customers** | Customer master data | 400 (50 per bank × 8 banks) |
| **accounts** | Bank accounts | ~800 (1-3 per customer) |
| **transactions** | Transaction history | ~8,000 (5-20 per account) |
| **fraud_events** | Detected fraud events | ~400 (50 per bank) |
| **internal_kpis** | Daily KPI metrics | ~6,480 (90 days × 9 metrics × 8 banks) |
| **intelligence_metrics** | Intelligence platform metrics | Auto-generated |
| **fraud_patterns** | Detected fraud patterns | 40 (5 per bank) |
| **datasets** | Uploaded file metadata | Empty (for future uploads) |

### **Indexes Created**

- `idx_transactions_customer_time` - Fast customer transaction queries
- `idx_transactions_bank_time` - Fast bank transaction queries
- `idx_fraud_events_customer` - Fast fraud event lookups
- `idx_fraud_events_bank` - Fast bank fraud queries
- `idx_internal_kpis_metric_date` - Fast KPI time-series queries
- `idx_intelligence_metrics_bank_date` - Fast intelligence queries

---

## 🏦 **Data Per Bank**

Each of the **8 banks** gets:

- ✅ **50 customers** with realistic profiles
- ✅ **~100 accounts** (savings, checking, business, premium)
- ✅ **~1,000 transactions** (90 days of history)
- ✅ **~50 fraud events** (various risk levels)
- ✅ **810 KPI records** (90 days × 9 metrics)
- ✅ **5 fraud patterns** (velocity bursts, channel concentration, etc.)

**Banks:**
- Dashen
- Abyssinia
- Awash
- CBE
- Amhara
- Zemen
- Tsedey
- Nib

---

## 📋 **Table Schemas**

### **1. Customers**
```sql
CREATE TABLE customers (
    customer_id TEXT PRIMARY KEY,
    bank_id TEXT NOT NULL,
    name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    account_type TEXT NOT NULL,
    risk_score INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

**Sample Data:**
```
customer_id        | bank_id | name         | account_type | risk_score
-------------------|---------|--------------|--------------|------------
dashen-cust-0001   | dashen  | Customer 1   | savings      | 45
zemen-cust-0001    | zemen   | Customer 1   | premium      | 23
```

---

### **2. Accounts**
```sql
CREATE TABLE accounts (
    account_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL REFERENCES customers(customer_id),
    bank_id TEXT NOT NULL,
    account_type TEXT NOT NULL,
    balance NUMERIC NOT NULL DEFAULT 0,
    currency TEXT NOT NULL DEFAULT 'ETB',
    status TEXT NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

**Sample Data:**
```
account_id              | customer_id      | account_type | balance
------------------------|------------------|--------------|----------
dashen-cust-0001-acc-1  | dashen-cust-0001 | savings      | 125000.50
dashen-cust-0001-acc-2  | dashen-cust-0001 | checking     | 45000.00
```

---

### **3. Transactions**
```sql
CREATE TABLE transactions (
    tx_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL REFERENCES customers(customer_id),
    account_id TEXT REFERENCES accounts(account_id),
    bank_id TEXT NOT NULL,
    tx_timestamp TIMESTAMPTZ NOT NULL,
    amount NUMERIC NOT NULL,
    currency TEXT NOT NULL DEFAULT 'ETB',
    direction TEXT NOT NULL CHECK (direction IN ('debit','credit')),
    channel TEXT NOT NULL,
    merchant TEXT,
    category TEXT,
    location_city TEXT,
    device_id TEXT,
    ip_address TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

**Sample Data:**
```
tx_id          | customer_id      | amount    | channel | category  | location_city
---------------|------------------|-----------|---------|-----------|---------------
tx-dashen-12345| dashen-cust-0001 | 5000.00   | mobile  | transfer  | Addis Ababa
tx-dashen-12346| dashen-cust-0001 | 15000.00  | atm     | withdrawal| Dire Dawa
```

---

### **4. Fraud Events**
```sql
CREATE TABLE fraud_events (
    event_id TEXT PRIMARY KEY,
    tx_id TEXT REFERENCES transactions(tx_id),
    customer_id TEXT NOT NULL REFERENCES customers(customer_id),
    bank_id TEXT NOT NULL,
    event_timestamp TIMESTAMPTZ NOT NULL,
    amount NUMERIC NOT NULL,
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
```

**Sample Data:**
```
event_id         | risk_score | risk_level | fraud_reasons                           | is_confirmed
-----------------|------------|------------|-----------------------------------------|-------------
fraud-dashen-001 | 85         | high       | {unusually_large_amount,new_device}     | false
fraud-dashen-002 | 55         | medium     | {suspicious_channel_mix}                | false
```

---

### **5. Internal KPIs**
```sql
CREATE TABLE internal_kpis (
    kpi_id SERIAL PRIMARY KEY,
    bank_id TEXT NOT NULL,
    kpi_date DATE NOT NULL,
    metric_name TEXT NOT NULL,
    metric_value NUMERIC NOT NULL,
    segment_type TEXT,
    segment_value TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(bank_id, kpi_date, metric_name, segment_type, segment_value)
);
```

**Metrics Tracked:**
- `deposits` - Total deposits (ETB)
- `loans` - Total loans (ETB)
- `npl_proxy` - Non-performing loan ratio (%)
- `digital_adoption` - Digital banking adoption rate (0-1)
- `customer_count` - Total active customers
- `transaction_volume` - Daily transaction count
- `revenue` - Daily revenue (ETB)
- `cost_to_income_ratio` - Cost-to-income ratio (%)
- `customer_satisfaction` - Customer satisfaction score (1-5)

**Sample Data:**
```
bank_id | kpi_date   | metric_name  | metric_value
--------|------------|--------------|-------------
dashen  | 2026-08-18 | deposits     | 45200000000
dashen  | 2026-08-18 | npl_proxy    | 2.1
zemen   | 2026-08-18 | deposits     | 38500000000
```

---

### **6. Fraud Patterns**
```sql
CREATE TABLE fraud_patterns (
    pattern_id TEXT PRIMARY KEY,
    bank_id TEXT NOT NULL,
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
```

**Pattern Types:**
- `velocity_burst` - Rapid transaction velocity
- `channel_concentration` - Unusual channel concentration
- `unusual_time_pattern` - Transactions during unusual hours
- `amount_structuring` - Amount structuring (just below thresholds)
- `geographic_anomaly` - Geographic anomalies

**Sample Data:**
```
pattern_id              | pattern_type     | severity | detection_count
------------------------|------------------|----------|----------------
dashen-pat-velocity     | velocity_burst   | high     | 23
zemen-pat-time-anomaly  | unusual_time     | medium   | 15
```

---

## 🧪 **Testing the Database**

### **1. Check Connection**
```bash
# Using Docker
docker-compose exec postgres psql -U demo_user -d fraudshield_demo -c "SELECT version();"

# Local
psql fraudshield_demo -c "SELECT version();"
```

### **2. Verify Tables**
```sql
-- List all tables
\dt

-- Count records
SELECT 
    'customers' as table_name, COUNT(*) as count FROM customers
UNION ALL
SELECT 'accounts', COUNT(*) FROM accounts
UNION ALL
SELECT 'transactions', COUNT(*) FROM transactions
UNION ALL
SELECT 'fraud_events', COUNT(*) FROM fraud_events
UNION ALL
SELECT 'internal_kpis', COUNT(*) FROM internal_kpis
UNION ALL
SELECT 'fraud_patterns', COUNT(*) FROM fraud_patterns;
```

### **3. Sample Queries**

#### **Get Customer Transactions**
```sql
SELECT 
    t.tx_id,
    t.tx_timestamp,
    t.amount,
    t.channel,
    t.category
FROM transactions t
WHERE t.customer_id = 'dashen-cust-0001'
ORDER BY t.tx_timestamp DESC
LIMIT 10;
```

#### **Get Fraud Events by Risk Level**
```sql
SELECT 
    risk_level,
    COUNT(*) as count,
    AVG(risk_score) as avg_score
FROM fraud_events
WHERE bank_id = 'dashen'
GROUP BY risk_level
ORDER BY avg_score DESC;
```

#### **Get KPI Trends**
```sql
SELECT 
    kpi_date,
    metric_value as deposits
FROM internal_kpis
WHERE bank_id = 'dashen'
  AND metric_name = 'deposits'
ORDER BY kpi_date DESC
LIMIT 30;
```

#### **Get Active Fraud Patterns**
```sql
SELECT 
    pattern_name,
    severity,
    detection_count,
    last_detected
FROM fraud_patterns
WHERE bank_id = 'dashen'
  AND is_active = TRUE
ORDER BY severity DESC, detection_count DESC;
```

---

## 🔄 **Resetting the Database**

### **Complete Reset**
```bash
# Using Docker
docker-compose down -v  # Remove volumes
docker-compose up -d
sleep 10
docker-compose exec fraudshield-api python setup_database.py

# Local
dropdb fraudshield_demo
createdb fraudshield_demo
python3 setup_database.py
```

### **Re-seed Data Only**
```bash
# Delete data but keep tables
docker-compose exec postgres psql -U demo_user -d fraudshield_demo -c "
TRUNCATE customers, accounts, transactions, fraud_events, 
         internal_kpis, fraud_patterns, intelligence_metrics CASCADE;
"

# Re-run seed
docker-compose exec fraudshield-api python setup_database.py
```

---

## 📊 **Using the Data**

### **Analytics Queries**

Now you can use the Intelligence Platform with **real database data**:

```bash
# Get KPIs from database
curl -X POST http://localhost:8000/api/internal/insights/kpis

# Query specific metrics
curl -X POST http://localhost:8000/api/internal/insights/query \
  -H "Content-Type: application/json" \
  -d '{
    "metricName": "deposits",
    "timeRange": {"start": "2026-07-01", "end": "2026-08-18"}
  }'
```

### **Fraud Monitoring**

Query fraud events:

```bash
# Get fraud alerts (will use database if available)
curl -X POST http://localhost:8000/api/fraud/alerts \
  -H "Content-Type: application/json" \
  -d '{
    "events": [...]
  }'
```

### **Natural Language Analytics**

Ask questions about your data:

```bash
# The analytics agent can now query real database data
curl -X POST http://localhost:8000/api/chat \
  -H "X-Bank-Id: dashen" \
  -d '{"message": "What are our deposits?"}'
```

---

## 🔧 **Troubleshooting**

### **Connection Refused**
```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Check logs
docker-compose logs postgres

# Restart
docker-compose restart postgres
```

### **Permission Denied**
```bash
# Make setup script executable
chmod +x setup_database.py
```

### **Database Already Exists**
```bash
# Drop and recreate
docker-compose exec postgres psql -U demo_user -c "DROP DATABASE fraudshield_demo;"
docker-compose exec postgres psql -U demo_user -c "CREATE DATABASE fraudshield_demo;"
docker-compose exec fraudshield-api python setup_database.py
```

---

## ✅ **Summary**

After running the setup, you'll have:

| Component | Count | Description |
|-----------|-------|-------------|
| **Banks** | 8 | Dashen, Abyssinia, Awash, CBE, Amhara, Zemen, Tsedey, Nib |
| **Customers** | 400 | 50 per bank with realistic profiles |
| **Accounts** | ~800 | 1-3 accounts per customer |
| **Transactions** | ~8,000 | 90 days of transaction history |
| **Fraud Events** | ~400 | Various risk levels and patterns |
| **KPI Records** | ~6,480 | 90 days of daily metrics |
| **Fraud Patterns** | 40 | 5 patterns per bank |

**All data is:**
- ✅ Bank-specific (isolated by `bank_id`)
- ✅ Realistic (proper amounts, dates, patterns)
- ✅ Ready for analytics
- ✅ Ready for fraud detection
- ✅ Ready for demos

---

## 🎉 **You're Ready!**

Your database is now set up with comprehensive seed data for:
1. ✅ **Analytics** - KPIs, metrics, trends
2. ✅ **Fraud Monitoring** - Events, patterns, alerts
3. ✅ **Multi-Bank** - Data for all 8 banks
4. ✅ **Production-Ready** - Proper indexes, constraints

**Start using it:**
```bash
# Start everything
docker-compose up -d

# Test analytics
curl http://localhost:8000/api/internal/insights/kpis

# Test fraud detection
curl -X POST http://localhost:8000/api/fraud/monitor -d '{...}'

# Ask questions
curl -X POST http://localhost:8000/api/chat -d '{"message": "What are our deposits?"}'
```

🚀 **Happy demoing!**
