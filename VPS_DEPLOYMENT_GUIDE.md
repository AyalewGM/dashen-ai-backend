# 🚀 VPS Deployment & Database Seeding Guide

## 📋 **Overview**

This guide covers deploying your application to a remote VPS and seeding the PostgreSQL database.

---

## 🎯 **Method 1: Automated Deployment (Recommended)**

### **Quick Deploy:**

```bash
# Make script executable
chmod +x deploy_and_seed.sh

# Deploy and seed in one command
./deploy_and_seed.sh user@your-vps-ip
```

This script will:
1. ✅ Deploy your application code
2. ✅ Setup PostgreSQL database
3. ✅ Run seeding script
4. ✅ Verify data

---

## 🎯 **Method 2: Manual Step-by-Step**

### **Step 1: Setup VPS**

SSH into your VPS:
```bash
ssh user@your-vps-ip
```

### **Step 2: Install Dependencies**

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install PostgreSQL
sudo apt install postgresql postgresql-contrib -y

# Install Docker (if using Docker deployment)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt install docker-compose -y

# Install Python (if running directly)
sudo apt install python3 python3-pip -y
```

### **Step 3: Clone Repository**

```bash
# Create app directory
sudo mkdir -p /opt/dashen-ai-backend
sudo chown $USER:$USER /opt/dashen-ai-backend

# Clone repository
cd /opt/dashen-ai-backend
git clone https://github.com/your-repo/dashen-ai-backend.git .
```

### **Step 4: Setup PostgreSQL Database**

```bash
# Create database and user
sudo -u postgres psql << EOF
CREATE USER demo_user WITH PASSWORD 'demo_password';
CREATE DATABASE fraudshield_demo OWNER demo_user;
GRANT ALL PRIVILEGES ON DATABASE fraudshield_demo TO demo_user;

-- Connect to database
\c fraudshield_demo

-- Grant schema privileges
GRANT ALL ON SCHEMA public TO demo_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO demo_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO demo_user;
EOF
```

### **Step 5: Configure Environment**

```bash
# Create .env file
cat > .env << EOF
DATABASE_URL=postgresql://demo_user:demo_password@localhost:5432/fraudshield_demo
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL_NAME=gemini-2.0-flash-exp
ALLOWED_ORIGINS=http://your-frontend-domain.com
EOF
```

### **Step 6: Deploy Application**

**Option A: Using Docker**

```bash
# Build and start containers
docker-compose -f docker-compose.yml up -d

# Check status
docker-compose ps
```

**Option B: Direct Python**

```bash
# Install dependencies
pip3 install -r requirements.txt

# Run with gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

### **Step 7: Seed Database**

**If using Docker:**

```bash
# Copy seed script to container
docker cp app/seed_db.py fraudshield-api-local:/app/seed_db.py

# Run seeding
docker exec fraudshield-api-local python seed_db.py
```

**If running directly:**

```bash
# Set environment
export DATABASE_URL=postgresql://demo_user:demo_password@localhost:5432/fraudshield_demo
export PYTHONPATH=/opt/dashen-ai-backend

# Run seeding
python3 app/seed_db.py
```

### **Step 8: Verify Data**

```bash
# Check database
PGPASSWORD=demo_password psql -h localhost -U demo_user -d fraudshield_demo -c "
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

Expected output:
```
 table_name    | count 
---------------+-------
 customers     |   500
 transactions  | 10000
 accounts      |  1000
 internal_kpis |  9000
```

---

## 🎯 **Method 3: Seed from Local Backup**

### **Step 1: Export from Local**

On your local machine:
```bash
# Export data only (no schema)
PGPASSWORD=demo_password pg_dump -h localhost -U demo_user \
  --data-only \
  --no-owner \
  --no-privileges \
  fraudshield_demo > seed_data.sql

# Or export everything (schema + data)
PGPASSWORD=demo_password pg_dump -h localhost -U demo_user \
  fraudshield_demo > full_backup.sql
```

### **Step 2: Copy to VPS**

```bash
# Copy SQL file to VPS
scp seed_data.sql user@your-vps-ip:/tmp/
```

### **Step 3: Import on VPS**

```bash
# SSH into VPS
ssh user@your-vps-ip

# Import data
PGPASSWORD=demo_password psql -h localhost -U demo_user \
  fraudshield_demo < /tmp/seed_data.sql

# Verify
PGPASSWORD=demo_password psql -h localhost -U demo_user \
  fraudshield_demo -c "SELECT COUNT(*) FROM customers;"

# Clean up
rm /tmp/seed_data.sql
```

---

## 🔒 **Security Considerations**

### **1. Change Default Credentials**

```bash
# On VPS, update database password
sudo -u postgres psql << EOF
ALTER USER demo_user WITH PASSWORD 'strong_random_password_here';
EOF

# Update .env file
sed -i 's/demo_password/strong_random_password_here/g' .env

# Restart application
docker-compose restart  # or restart your service
```

### **2. Configure Firewall**

```bash
# Allow only necessary ports
sudo ufw allow 22      # SSH
sudo ufw allow 80      # HTTP
sudo ufw allow 443     # HTTPS
sudo ufw allow 8000    # API (or use nginx reverse proxy)
sudo ufw enable
```

### **3. Setup SSL/TLS**

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx -y

# Get SSL certificate
sudo certbot --nginx -d your-domain.com
```

---

## 🔄 **Re-seeding Database**

### **Clear and Re-seed:**

```bash
# SSH into VPS
ssh user@your-vps-ip

# Clear existing data
PGPASSWORD=demo_password psql -h localhost -U demo_user -d fraudshield_demo << EOF
TRUNCATE TABLE transactions CASCADE;
TRUNCATE TABLE accounts CASCADE;
TRUNCATE TABLE customers CASCADE;
TRUNCATE TABLE internal_kpis CASCADE;
EOF

# Re-run seeding
docker exec fraudshield-api-local python seed_db.py
# OR
python3 app/seed_db.py
```

---

## 📊 **Monitoring & Maintenance**

### **Check Application Status:**

```bash
# Docker
docker-compose ps
docker logs fraudshield-api-local --tail 50

# Direct
systemctl status your-app-service
```

### **Check Database:**

```bash
# Connect to database
PGPASSWORD=demo_password psql -h localhost -U demo_user fraudshield_demo

# Check table sizes
SELECT 
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### **Backup Database:**

```bash
# Create backup
PGPASSWORD=demo_password pg_dump -h localhost -U demo_user \
  fraudshield_demo > backup_$(date +%Y%m%d_%H%M%S).sql

# Compress backup
gzip backup_*.sql

# Copy to local machine
scp user@vps-ip:/path/to/backup_*.sql.gz ./
```

---

## 🚀 **Quick Reference Commands**

### **Deploy:**
```bash
./deploy_and_seed.sh user@vps-ip
```

### **Seed Database:**
```bash
# Docker
docker exec fraudshield-api-local python seed_db.py

# Direct
python3 app/seed_db.py
```

### **Verify Data:**
```bash
PGPASSWORD=demo_password psql -h localhost -U demo_user -d fraudshield_demo \
  -c "SELECT COUNT(*) FROM customers;"
```

### **Check Logs:**
```bash
docker logs fraudshield-api-local --tail 100 -f
```

### **Restart Application:**
```bash
docker-compose restart
```

---

## ✅ **Deployment Checklist**

- [ ] VPS setup complete
- [ ] PostgreSQL installed and configured
- [ ] Application deployed (Docker or direct)
- [ ] Database created
- [ ] Environment variables configured
- [ ] Database seeded
- [ ] Data verified
- [ ] Firewall configured
- [ ] SSL/TLS setup (optional)
- [ ] Backup strategy in place

---

## 🎯 **Summary**

**Easiest Method:**
```bash
./deploy_and_seed.sh user@vps-ip
```

**Manual Method:**
1. Setup VPS and PostgreSQL
2. Deploy application
3. Run seed script on VPS
4. Verify data

**Backup Method:**
1. Export from local database
2. Copy to VPS
3. Import on VPS

**Your database will be seeded on the VPS with the same sample data!** 🎉🚀
