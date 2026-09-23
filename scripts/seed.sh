#!/bin/bash

# Database Seeding Script for Goozam AI Platform

cd "$(dirname "$0")/.."

echo "🌱 Goozam AI Platform - Database Seeding"
echo "========================================"
echo ""

# Check if docker-compose is running
if ! docker-compose -f docker-compose.local.yml ps | grep -q "fraudshield-db-local.*Up"; then
    echo "⚠️  Database container is not running!"
    echo "Starting containers..."
    docker-compose -f docker-compose.local.yml up -d
    echo "Waiting for containers to be ready..."
    sleep 10
elif ! docker-compose -f docker-compose.local.yml ps | grep -q "fraudshield-api-local.*Up"; then
    echo "⚠️  API container is not running!"
    echo "Starting API container..."
    docker-compose -f docker-compose.local.yml up -d fraudshield-api-local
    echo "Waiting for API to be ready..."
    sleep 5
fi

# Run seeding script inside Docker container
if [ "$1" == "--clear" ]; then
    echo "🗑️  Clearing existing data and seeding..."
    docker-compose -f docker-compose.local.yml exec fraudshield-api-local python scripts/seed_database.py --clear
elif [ "$1" == "--bank" ] && [ -n "$2" ]; then
    echo "🏦 Seeding data for bank: $2"
    docker-compose -f docker-compose.local.yml exec fraudshield-api-local python scripts/seed_database.py --bank "$2"
elif [ "$1" == "--help" ] || [ "$1" == "-h" ]; then
    echo "Usage:"
    echo "  ./scripts/seed.sh              # Seed all banks"
    echo "  ./scripts/seed.sh --clear      # Clear and seed all banks"
    echo "  ./scripts/seed.sh --bank dashen # Seed specific bank"
    echo ""
    echo "Available banks:"
    echo "  dashen, tsehay, birhan, cbe, awash, wegagen, abyssinia, nib, oromia, zemen"
else
    echo "🌱 Seeding all banks..."
    docker-compose -f docker-compose.local.yml exec fraudshield-api-local python scripts/seed_database.py
fi

echo ""
echo "✅ Done!"
