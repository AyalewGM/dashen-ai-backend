# 🚀 Quick Start - Local PostgreSQL

## ✅ **Database Already Created!**

Your local PostgreSQL now has `fraudshield_demo` database ready!

---

## 📊 **Connection Details:**

```
Host:     localhost
Port:     5432
Database: fraudshield_demo
Username: demo_user
Password: demo_password
```

---

## 🌱 **Seed the Database**

### **Option 1: Using Docker (Easiest)**

Since dependencies are already in Docker:

```bash
# 1. Stop Docker database (we're using local now)
docker-compose -f docker-compose.local.yml stop postgres

# 2. Update API to use local database
# Edit docker-compose.local.yml, change DATABASE_URL to:
# DATABASE_URL=postgresql://demo_user:demo_password@host.docker.internal:5432/fraudshield_demo

# 3. Restart API
docker-compose -f docker-compose.local.yml up -d fraudshield-api

# 4. Copy seed script to container
docker cp app/seed_db.py fraudshield-api-local:/app/seed_db.py

# 5. Run seeding
docker exec fraudshield-api-local python seed_db.py
```

### **Option 2: Install Dependencies Locally**

```bash
# Install Python dependencies
pip3 install psycopg2-binary

# Set environment
export DATABASE_URL=postgresql://demo_user:demo_password@localhost:5432/fraudshield_demo
export PYTHONPATH=/Users/ayalew/Projects/dashen-ai-backend

# Run seeding
python3 app/seed_db.py
```

---

## 🔍 **Verify Database**

```bash
# Check connection
PGPASSWORD=demo_password psql -h localhost -U demo_user -d fraudshield_demo -c "SELECT version();"

# Check tables (after seeding)
PGPASSWORD=demo_password psql -h localhost -U demo_user -d fraudshield_demo -c "\dt"

# Check data (after seeding)
PGPASSWORD=demo_password psql -h localhost -U demo_user -d fraudshield_demo -c "SELECT COUNT(*) FROM customers;"
```

---

## 🎯 **Recommended: Use Docker to Seed**

Since Docker already has all dependencies:

```bash
# 1. Update docker-compose.local.yml
#    Change line 19 from:
#      - DATABASE_URL=postgresql://demo_user:demo_password@postgres:5432/fraudshield_demo
#    To:
#      - DATABASE_URL=postgresql://demo_user:demo_password@host.docker.internal:5432/fraudshield_demo

# 2. Stop Docker database
docker-compose -f docker-compose.local.yml stop postgres

# 3. Restart API
docker-compose -f docker-compose.local.yml restart fraudshield-api

# 4. Wait for API to be ready
sleep 5

# 5. Copy and run seed script
docker cp app/seed_db.py fraudshield-api-local:/app/seed_db.py
docker exec fraudshield-api-local python seed_db.py
```

---

## ✅ **Summary**

**What's Ready:**
- ✅ Local PostgreSQL running on port 5432
- ✅ Database `fraudshield_demo` created
- ✅ User `demo_user` with password `demo_password`
- ⏳ Need to seed data

**Next Step:**
Choose Option 1 (Docker) or Option 2 (Local) to seed the database!

---

**Your local PostgreSQL is ready - just need to seed it!** 🌱🗄️
