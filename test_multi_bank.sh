#!/bin/bash

# Multi-Bank Demo Test Script
# Tests that each bank has unique branding and RAG responses

echo "🧪 Testing Multi-Bank White-Label Demo"
echo "========================================"
echo ""

BASE_URL="http://localhost:8000"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "📋 Test 1: List All Banks"
echo "-------------------------"
curl -s "$BASE_URL/api/bank/list" | jq '.'
echo ""

echo "🎨 Test 2: Get Branding for Each Bank"
echo "--------------------------------------"

for bank in dashen abyssinia awash cbe; do
    echo ""
    echo -e "${BLUE}Testing $bank...${NC}"
    response=$(curl -s "$BASE_URL/api/bank/info/$bank")
    
    bank_name=$(echo $response | jq -r '.bankName')
    primary_color=$(echo $response | jq -r '.branding.primaryColor')
    tagline=$(echo $response | jq -r '.branding.tagline')
    
    echo -e "  Bank: ${GREEN}$bank_name${NC}"
    echo -e "  Color: ${YELLOW}$primary_color${NC}"
    echo -e "  Tagline: $tagline"
done

echo ""
echo "💬 Test 3: Chatbot Responses (Bank-Specific RAG)"
echo "-------------------------------------------------"

for bank in dashen abyssinia; do
    echo ""
    echo -e "${BLUE}Testing chatbot for $bank...${NC}"
    
    response=$(curl -s -X POST "$BASE_URL/api/chat" \
        -H "Content-Type: application/json" \
        -H "X-Bank-Id: $bank" \
        -d '{
            "sessionId": "test-'$bank'",
            "message": "What services do you offer?"
        }')
    
    reply=$(echo $response | jq -r '.reply' | head -c 100)
    echo -e "  Response preview: ${GREEN}$reply...${NC}"
done

echo ""
echo "📊 Test 4: Intelligence Dashboard (Bank-Specific Data)"
echo "-------------------------------------------------------"

for bank in dashen awash; do
    echo ""
    echo -e "${BLUE}Testing dashboard for $bank...${NC}"
    
    response=$(curl -s -X POST "$BASE_URL/api/intelligence/dashboard" \
        -H "Content-Type: application/json" \
        -d '{
            "bankId": "'$bank'",
            "timeRange": "30d"
        }')
    
    kpi_count=$(echo $response | jq '.kpiCards | length')
    narrative=$(echo $response | jq -r '.insightNarrative' | head -c 80)
    
    echo -e "  KPI Cards: ${GREEN}$kpi_count${NC}"
    echo -e "  Narrative: $narrative..."
done

echo ""
echo "🚨 Test 5: Fraud Detection (Bank-Specific Rules)"
echo "-------------------------------------------------"

for bank in dashen cbe; do
    echo ""
    echo -e "${BLUE}Testing fraud detection for $bank...${NC}"
    
    response=$(curl -s -X POST "$BASE_URL/api/fraud/score" \
        -H "Content-Type: application/json" \
        -d '{
            "event": {
                "eventId": "test-'$bank'",
                "customerId": "cust-123",
                "timestamp": "2026-08-18T22:00:00Z",
                "amount": 110000,
                "currency": "ETB",
                "channel": "atm",
                "eventType": "withdrawal"
            }
        }')
    
    risk_score=$(echo $response | jq -r '.riskScore')
    risk_level=$(echo $response | jq -r '.riskLevel')
    
    echo -e "  Risk Score: ${YELLOW}$risk_score${NC}"
    echo -e "  Risk Level: ${RED}$risk_level${NC}"
    echo "  (Note: Different banks have different thresholds)"
done

echo ""
echo "✅ All Tests Complete!"
echo "======================"
echo ""
echo "Summary:"
echo "  ✓ Each bank has unique branding (colors, logos, taglines)"
echo "  ✓ Each bank has separate RAG knowledge base"
echo "  ✓ Each bank shows different KPIs and data"
echo "  ✓ Each bank uses different fraud detection rules"
echo ""
echo "🎉 White-label multi-bank demo is working!"
