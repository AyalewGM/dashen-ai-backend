# 📊 Natural Language Analytics Q&A Guide

## 🎯 **Overview**

Your chatbot now has **dual capabilities**:

1. **General Banking Questions** - Uses RAG (bank website knowledge)
2. **Analytics Questions** - Uses Intelligence Platform (real data)

The system **automatically detects** which type of question you're asking and routes it appropriately!

---

## ✅ **What's New: Analytics Agent**

### **How It Works**

```
User asks: "What's our deposit growth?"
    ↓
Analytics Agent detects keywords: "deposit", "growth"
    ↓
Routes to Intelligence Platform
    ↓
Fetches real KPI data
    ↓
Returns natural language answer
```

---

## 🗣️ **Example Analytics Questions**

### **1. Current Metrics (Dashboard Queries)**

```bash
# Deposits
curl -X POST http://localhost:8000/api/chat \
  -H "X-Bank-Id: dashen" \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "demo",
    "message": "What are our current deposits?"
  }'
```

**Response:**
```
Total Deposits is currently 52.1B ETB, +3.5% from last period. This shows an up trend.
```

**More examples:**
- "How many active customers do we have?"
- "What's our NPL ratio?"
- "Show me our digital adoption rate"
- "What's the current loan portfolio?"
- "How many fraud alerts do we have?"

---

### **2. Forecasts & Predictions**

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "X-Bank-Id: zemen" \
  -d '{
    "sessionId": "demo",
    "message": "Forecast deposit growth for next 30 days"
  }'
```

**Response:**
```
Based on predictive analytics:

• Current forecast: 52.3
• 30-day outlook: 58.7
• Trend: increasing
• Confidence: 87%

Forecast shows increasing trend with strong momentum in the market. 
Digital banking adoption is accelerating.

Key risks: Market volatility, Operational capacity constraints
```

**More examples:**
- "Predict customer acquisition for next quarter"
- "What's the forecast for digital adoption?"
- "Will loan demand increase next month?"
- "Forecast revenue for 60 days"

---

### **3. Strategic Decisions**

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "X-Bank-Id: tsedey" \
  -d '{
    "sessionId": "demo",
    "message": "Should we expand our SME lending program?"
  }'
```

**Response:**
```
Based on current market conditions and Tsedey Bank's strong capital position, 
expanding SME lending presents a strategic opportunity...

**Recommended Option:** Expand SME lending program
• Impact Score: 85/100
• Risk Level: medium
• Expected Outcome: 15-20% increase in loan portfolio within 12 months

**Pros:**
  ✓ High demand segment with limited competition
  ✓ Better risk-adjusted returns
  ✓ Supports economic growth

**Cons:**
  ✗ Higher default risk than corporate
  ✗ Requires specialized underwriting
  ✗ Longer processing times
```

**More examples:**
- "Should we launch a mobile banking app?"
- "Recommend strategies for digital transformation"
- "Should we expand to new branches?"
- "What if we invest in AI fraud detection?"

---

### **4. General Analytics Overview**

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "X-Bank-Id: nib" \
  -d '{
    "sessionId": "demo",
    "message": "Give me an analytics overview"
  }'
```

**Response:**
```
Here's your current performance overview:

• Total Deposits: 58.3B ETB (+4.2%)
• Active Customers: 1.6M (+2.8%)
• Digital Adoption: 71% (+7%)

Nib International Bank shows strong performance across key metrics. 
Digital banking adoption is accelerating, with mobile transactions up 12% 
this month. Loan portfolio growth is steady at 3.1%, and NPL ratio has 
improved to 2.0%. Continue monitoring fraud alerts (15 active) and maintain 
focus on customer satisfaction initiatives.
```

---

## 🌍 **Multilingual Analytics**

Works in **5+ languages**!

### **English**
```json
{
  "message": "What's our deposit growth?"
}
```

### **Amharic**
```json
{
  "message": "የእኛ የተቀማጭ ገንዘብ እድገት ምን ያህል ነው?"
}
```

### **Oromo**
```json
{
  "message": "Guddina kuusaa keenyaa meeqa?"
}
```

**All return answers in the requested language!**

---

## 🔍 **How Detection Works**

The Analytics Agent detects questions using **keyword matching**:

### **Analytics Keywords:**
- **Metrics**: deposit, loan, npl, customer, revenue, profit, growth, trend, kpi
- **Questions**: how much, how many, what is, show me, tell me about
- **Analytics terms**: analytics, data, statistics, forecast, predict
- **Comparisons**: compare, versus, difference, better, worse
- **Time-based**: this month, this quarter, last month, today, weekly

### **Examples:**

| Question | Detected As | Routed To |
|----------|-------------|-----------|
| "What are your services?" | General Banking | RAG (Website) |
| "What's our deposit growth?" | Analytics | Intelligence Platform |
| "How do I open an account?" | General Banking | RAG (Website) |
| "Show me NPL trends" | Analytics | Intelligence Platform |
| "What are your loan rates?" | General Banking | RAG (Website) |
| "Forecast customer acquisition" | Analytics | Intelligence Platform |

---

## 🎯 **Use Cases**

### **For Bank Executives:**
```bash
# Morning briefing
"Give me an analytics overview"

# Strategic planning
"Should we expand SME lending?"

# Performance monitoring
"What's our NPL ratio?"
"Show me digital adoption trends"
```

### **For Analytics Teams:**
```bash
# Data exploration
"What's our deposit growth this month?"
"Compare customer acquisition vs last quarter"

# Forecasting
"Predict revenue for next 90 days"
"Forecast loan demand"

# Risk monitoring
"How many fraud alerts do we have?"
"What's the NPL trend?"
```

### **For Branch Managers:**
```bash
# Performance check
"What are our current deposits?"
"How many active customers?"

# Planning
"Should we invest in digital banking?"
```

---

## 🧪 **Testing All Capabilities**

### **Test Script:**

```bash
#!/bin/bash

BANK_ID="dashen"
BASE_URL="http://localhost:8000/api/chat"

echo "🧪 Testing Analytics Q&A"
echo "======================="

# Test 1: Current Metrics
echo -e "\n📊 Test 1: Current Deposits"
curl -s -X POST $BASE_URL \
  -H "X-Bank-Id: $BANK_ID" \
  -H "Content-Type: application/json" \
  -d '{"sessionId": "test", "message": "What are our current deposits?"}' \
  | jq -r '.reply'

# Test 2: Forecast
echo -e "\n📈 Test 2: Forecast"
curl -s -X POST $BASE_URL \
  -H "X-Bank-Id: $BANK_ID" \
  -d '{"sessionId": "test", "message": "Forecast deposit growth for 30 days"}' \
  | jq -r '.reply'

# Test 3: Strategic Decision
echo -e "\n🤔 Test 3: Strategic Decision"
curl -s -X POST $BASE_URL \
  -H "X-Bank-Id: $BANK_ID" \
  -d '{"sessionId": "test", "message": "Should we expand SME lending?"}' \
  | jq -r '.reply'

# Test 4: General Banking (should use RAG)
echo -e "\n🏦 Test 4: General Banking"
curl -s -X POST $BASE_URL \
  -H "X-Bank-Id: $BANK_ID" \
  -d '{"sessionId": "test", "message": "What are your services?"}' \
  | jq -r '.reply'

# Test 5: Multilingual Analytics
echo -e "\n🌍 Test 5: Multilingual (Amharic)"
curl -s -X POST $BASE_URL \
  -H "X-Bank-Id: $BANK_ID" \
  -H "Accept-Language: am" \
  -d '{"sessionId": "test", "message": "የእኛ የተቀማጭ ገንዘብ ምን ያህል ነው?"}' \
  | jq -r '.reply'

echo -e "\n✅ All tests complete!"
```

---

## 📊 **Comparison: Before vs After**

### **Before (Structured API Only)**

```bash
# Had to know exact endpoint
curl -X POST /api/intelligence/dashboard \
  -d '{"bankId": "dashen", "timeRange": "30d"}'

# Got JSON response
{
  "kpiCards": [
    {"title": "Total Deposits", "value": "52.1B ETB", ...}
  ]
}
```

**Problem:** Requires technical knowledge, not user-friendly

---

### **After (Natural Language)**

```bash
# Just ask naturally
curl -X POST /api/chat \
  -H "X-Bank-Id: dashen" \
  -d '{"message": "What are our deposits?"}'

# Get natural language answer
"Total Deposits is currently 52.1B ETB, +3.5% from last period. 
This shows an up trend."
```

**Benefit:** User-friendly, conversational, multilingual!

---

## ✅ **Summary**

### **What You Have Now:**

| Feature | Description | Example |
|---------|-------------|---------|
| **Dual-Mode Chatbot** | Auto-detects analytics vs general questions | "What's our NPL?" vs "What are your services?" |
| **Current Metrics** | Real-time KPI data | "Show me deposits", "How many customers?" |
| **Forecasts** | Predictive analytics | "Forecast deposit growth" |
| **Strategic Advice** | Decision support | "Should we expand SME lending?" |
| **Multilingual** | 5+ languages | English, Amharic, Oromo, Tigrinya, Somali |
| **Bank-Specific** | Each bank sees their data | Dashen, Zemen, Tsedey, Nib, etc. |

### **Benefits:**

✅ **User-Friendly** - No need to know API endpoints  
✅ **Conversational** - Ask questions naturally  
✅ **Intelligent** - Auto-routes to correct data source  
✅ **Multilingual** - Works in local languages  
✅ **Bank-Specific** - Personalized for each bank  
✅ **Production-Ready** - Error handling, logging  

---

## 🚀 **Demo Script**

### **Scenario 1: Executive Briefing**

```bash
# Morning briefing for Dashen Bank CEO
curl -X POST /api/chat -H "X-Bank-Id: dashen" \
  -d '{"message": "Give me an analytics overview"}'

# Check specific metric
curl -X POST /api/chat -H "X-Bank-Id: dashen" \
  -d '{"message": "What's our NPL ratio?"}'

# Strategic question
curl -X POST /api/chat -H "X-Bank-Id: dashen" \
  -d '{"message": "Should we invest in digital banking?"}'
```

### **Scenario 2: Multi-Bank Comparison**

```bash
# Dashen Bank
curl -X POST /api/chat -H "X-Bank-Id: dashen" \
  -d '{"message": "What are our deposits?"}'
# Response: "52.1B ETB"

# Zemen Bank (different data!)
curl -X POST /api/chat -H "X-Bank-Id: zemen" \
  -d '{"message": "What are our deposits?"}'
# Response: "58.3B ETB"
```

### **Scenario 3: Multilingual Demo**

```bash
# English
curl -X POST /api/chat -H "Accept-Language: en" \
  -d '{"message": "What's our deposit growth?"}'

# Amharic
curl -X POST /api/chat -H "Accept-Language: am" \
  -d '{"message": "የእኛ የተቀማጭ ገንዘብ እድገት ምን ያህል ነው?"}'

# Both get answers in their language!
```

---

## 🎉 **You Now Have Both!**

1. ✅ **Structured API** - For direct integration (`/api/intelligence/*`)
2. ✅ **Natural Language Q&A** - For user-friendly analytics (`/api/chat`)

**Perfect for demos!** 🚀
