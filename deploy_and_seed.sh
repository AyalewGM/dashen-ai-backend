#!/bin/bash

# Deployment and Seeding Script for Remote VPS
# Usage: ./deploy_and_seed.sh user@vps-ip

set -e  # Exit on error

VPS_HOST=$1
APP_PATH="/opt/dashen-ai-backend"  # Adjust to your VPS path

if [ -z "$VPS_HOST" ]; then
    echo "Usage: ./deploy_and_seed.sh user@vps-ip"
    exit 1
fi

echo "🚀 Deploying to $VPS_HOST..."
echo ""

# Step 1: Deploy application
echo "📦 Step 1: Deploying application code..."
ssh $VPS_HOST << 'ENDSSH'
cd /opt/dashen-ai-backend
git pull origin main
ENDSSH

# Step 2: Setup database (if not exists)
echo "🗄️  Step 2: Setting up database..."
ssh $VPS_HOST << 'ENDSSH'
sudo -u postgres psql << EOF
-- Create user if not exists
DO \$\$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_user WHERE usename = 'demo_user') THEN
    CREATE USER demo_user WITH PASSWORD 'demo_password';
  END IF;
END
\$\$;

-- Create database if not exists
SELECT 'CREATE DATABASE fraudshield_demo OWNER demo_user'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'fraudshield_demo')\gexec

GRANT ALL PRIVILEGES ON DATABASE fraudshield_demo TO demo_user;
EOF
ENDSSH

# Step 3: Copy seed script
echo "📋 Step 3: Copying seed script..."
scp app/seed_db.py $VPS_HOST:$APP_PATH/app/

# Step 4: Run seeding via Docker
echo "🌱 Step 4: Seeding database..."
ssh $VPS_HOST << ENDSSH
cd $APP_PATH

# If using Docker
if docker ps | grep -q fraudshield-api; then
    echo "Using Docker to seed..."
    docker cp app/seed_db.py fraudshield-api-local:/app/seed_db.py
    docker exec fraudshield-api-local python seed_db.py
else
    echo "Using direct Python to seed..."
    export DATABASE_URL=postgresql://demo_user:demo_password@localhost:5432/fraudshield_demo
    export PYTHONPATH=$APP_PATH
    python3 app/seed_db.py
fi
ENDSSH

# Step 5: Verify
echo "🔍 Step 5: Verifying data..."
ssh $VPS_HOST << 'ENDSSH'
PGPASSWORD=demo_password psql -h localhost -U demo_user -d fraudshield_demo -c "
SELECT 
  'customers' as table_name, COUNT(*) as count FROM customers
UNION ALL
SELECT 'transactions', COUNT(*) FROM transactions
UNION ALL
SELECT 'accounts', COUNT(*) FROM accounts;
"
ENDSSH

echo ""
echo "✅ Deployment and seeding complete!"
echo ""
