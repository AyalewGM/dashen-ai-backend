#!/bin/bash

# Setup Local PostgreSQL Database for Goozam AI Platform

echo "🗄️  Setting up local PostgreSQL database..."
echo ""

# Create user and database
psql postgres << EOF
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

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE fraudshield_demo TO demo_user;

\c fraudshield_demo

-- Grant schema privileges
GRANT ALL ON SCHEMA public TO demo_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO demo_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO demo_user;

EOF

echo ""
echo "✅ Database setup complete!"
echo ""
echo "📊 Connection Details:"
echo "   Host:     localhost"
echo "   Port:     5432"
echo "   Database: fraudshield_demo"
echo "   Username: demo_user"
echo "   Password: demo_password"
echo ""
echo "🔗 Connection String:"
echo "   postgresql://demo_user:demo_password@localhost:5432/fraudshield_demo"
echo ""
