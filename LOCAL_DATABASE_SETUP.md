# 🗄️ Local Database Setup Guide

## ✅ **Database is Now Exposed to Localhost!**

I've updated your `docker-compose.local.yml` to expose the PostgreSQL port to your host machine.

---

## 📊 **Database Connection Details:**

```
Host:     localhost (or 127.0.0.1)
Port:     5432
Database: fraudshield_demo
Username: demo_user
Password: demo_password
```

### **Connection String:**
```
postgresql://demo_user:demo_password@localhost:5432/fraudshield_demo
```

---

## 🎯 **Now You Can:**

### **1. Connect from Your Local Machine:**

```bash
# Using psql
psql -h localhost -p 5432 -U demo_user -d fraudshield_demo

# Password: demo_password
```

### **2. Use Database GUI Tools:**

**DBeaver:**
```
Host: localhost
Port: 5432
Database: fraudshield_demo
Username: demo_user
Password: demo_password
```

**pgAdmin:**
```
Host: localhost
Port: 5432
Database: fraudshield_demo
Username: demo_user
Password: demo_password
```

**TablePlus:**
```
Host: localhost
Port: 5432
Database: fraudshield_demo
User: demo_user
Password: demo_password
```

### **3. Run Python Scripts Locally:**

```python
import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="fraudshield_demo",
    user="demo_user",
    password="demo_password"
)

cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM customers")
print(cur.fetchone())
```

### **4. Run API Locally (Outside Docker):**

```bash
# Set environment variable
export DATABASE_URL=postgresql://demo_user:demo_password@localhost:5432/fraudshield_demo

# Run API locally
uvicorn main:app --reload --port 8000
```

---

## 💾 **Data Persistence:**

### **Your Data is SAFE!**

Even when you restart containers, your data persists in the Docker volume:

```bash
# Stop containers - DATA REMAINS
docker-compose -f docker-compose.local.yml down

# Start containers - DATA STILL THERE
docker-compose -f docker-compose.local.yml up -d
```

### **To Verify Data Persists:**

```bash
# 1. Check data exists
psql -h localhost -U demo_user -d fraudshield_demo -c "SELECT COUNT(*) FROM customers;"

# 2. Stop containers
docker-compose -f docker-compose.local.yml down

# 3. Start containers
docker-compose -f docker-compose.local.yml up -d

# 4. Check data again - STILL THERE!
psql -h localhost -U demo_user -d fraudshield_demo -c "SELECT COUNT(*) FROM customers;"
```

---

## ⚠️ **When Data is Lost:**

Data is ONLY lost if you:

### **1. Delete the Volume:**
```bash
# This DELETES all data
docker-compose -f docker-compose.local.yml down -v  # ⚠️ -v flag removes volumes!
```

### **2. Delete Volume Manually:**
```bash
# This DELETES all data
docker volume rm dashen-ai-backend_postgres_data
```

---

## 💾 **Backup & Restore:**

### **Backup Database:**

```bash
# Full backup
pg_dump -h localhost -U demo_user fraudshield_demo > backup_$(date +%Y%m%d).sql

# Compressed backup
pg_dump -h localhost -U demo_user fraudshield_demo | gzip > backup_$(date +%Y%m%d).sql.gz

# Backup specific tables
pg_dump -h localhost -U demo_user -t customers -t transactions fraudshield_demo > backup_tables.sql
```

### **Restore Database:**

```bash
# From SQL file
psql -h localhost -U demo_user fraudshield_demo < backup_20260827.sql

# From compressed file
gunzip -c backup_20260827.sql.gz | psql -h localhost -U demo_user fraudshield_demo
```

### **Copy Data to Another Database:**

```bash
# Dump from container
pg_dump -h localhost -U demo_user fraudshield_demo > data.sql

# Restore to new database
createdb -h localhost -U demo_user fraudshield_production
psql -h localhost -U demo_user fraudshield_production < data.sql
```

---

## 🔄 **Migration to Standalone PostgreSQL:**

If you want to use a completely local PostgreSQL (not Docker):

### **1. Install PostgreSQL:**

**Mac:**
```bash
brew install postgresql@15
brew services start postgresql@15
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql-15
sudo systemctl start postgresql
```

### **2. Create Database:**

```bash
# Switch to postgres user
sudo -u postgres psql

# Create user and database
CREATE USER demo_user WITH PASSWORD 'demo_password';
CREATE DATABASE fraudshield_demo OWNER demo_user;
GRANT ALL PRIVILEGES ON DATABASE fraudshield_demo TO demo_user;
\q
```

### **3. Migrate Data:**

```bash
# Export from Docker
pg_dump -h localhost -U demo_user fraudshield_demo > migration.sql

# Stop Docker database
docker-compose -f docker-compose.local.yml stop postgres

# Import to local PostgreSQL
psql -h localhost -U demo_user fraudshield_demo < migration.sql
```

### **4. Update Connection:**

```bash
# Same connection string works!
export DATABASE_URL=postgresql://demo_user:demo_password@localhost:5432/fraudshield_demo
```

---

## 🔍 **Verify Setup:**

### **1. Check Database is Accessible:**

```bash
psql -h localhost -U demo_user -d fraudshield_demo -c "SELECT version();"
```

### **2. Check Tables:**

```bash
psql -h localhost -U demo_user -d fraudshield_demo -c "\dt"
```

### **3. Check Data:**

```bash
psql -h localhost -U demo_user -d fraudshield_demo -c "
  SELECT 
    'customers' as table_name, COUNT(*) as count FROM customers
  UNION ALL
  SELECT 'transactions', COUNT(*) FROM transactions
  UNION ALL
  SELECT 'accounts', COUNT(*) FROM accounts
  UNION ALL
  SELECT 'internal_kpis', COUNT(*) FROM internal_kpis;
"
```

---

## 📊 **Database Management Commands:**

### **List All Databases:**
```bash
psql -h localhost -U demo_user -d postgres -c "\l"
```

### **List All Tables:**
```bash
psql -h localhost -U demo_user -d fraudshield_demo -c "\dt"
```

### **Describe Table:**
```bash
psql -h localhost -U demo_user -d fraudshield_demo -c "\d customers"
```

### **Check Database Size:**
```bash
psql -h localhost -U demo_user -d fraudshield_demo -c "
  SELECT pg_size_pretty(pg_database_size('fraudshield_demo'));
"
```

### **Check Table Sizes:**
```bash
psql -h localhost -U demo_user -d fraudshield_demo -c "
  SELECT 
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
  FROM pg_tables
  WHERE schemaname = 'public'
  ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"
```

---

## 🎯 **Summary:**

**What Changed:**
- ✅ Database now exposed on `localhost:5432`
- ✅ Can connect from your local machine
- ✅ Can use GUI tools (DBeaver, pgAdmin, TablePlus)
- ✅ Can run scripts locally
- ✅ Data still persists in Docker volume

**Connection Details:**
```
Host:     localhost
Port:     5432
Database: fraudshield_demo
Username: demo_user
Password: demo_password
```

**Data Persistence:**
- ✅ Data survives container restarts
- ✅ Data survives `docker-compose down`
- ❌ Data lost with `docker-compose down -v`

**Next Steps:**
1. Connect with your favorite database tool
2. Explore the seeded data
3. Run queries and analytics
4. Build your application!

---

**Your database is now accessible from localhost!** 🎉🗄️✨
