# 🐳 Docker Demo Guide

## Quick Start (3 Steps)

### **1. Setup Environment**
```bash
# Copy environment template
cp env.example .env

# Edit .env and add your Gemini API key
nano .env  # or use your favorite editor
```

Add your API key:
```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
GEMINI_MODEL_NAME=gemini-2.0-flash-exp
```

### **2. Start the Demo**
```bash
# Build and start containers
docker-compose up --build

# Or run in background
docker-compose up -d --build
```

### **3. Test It**
```bash
# Check if running
curl http://localhost:8000/api/bank/list

# Get bank branding
curl http://localhost:8000/api/bank/info/dashen

# Test chatbot
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -H "X-Bank-Id: dashen" \
  -d '{"sessionId": "demo", "message": "What are your services?"}'
```

**That's it! Your demo is running!** 🎉

---

## 🎯 **Demo Commands**

### **Start Demo**
```bash
docker-compose up
```

### **Stop Demo**
```bash
docker-compose down
```

### **Restart Demo**
```bash
docker-compose restart
```

### **View Logs**
```bash
# All logs
docker-compose logs -f

# Just the API
docker-compose logs -f fraudshield-api
```

### **Rebuild After Code Changes**
```bash
docker-compose up --build
```

---

## 🏦 **Test All 8 Banks**

```bash
# Test each bank's branding
for bank in dashen abyssinia awash cbe amhara zemen tsedey nib; do
    echo "Testing $bank..."
    curl -s http://localhost:8000/api/bank/info/$bank | jq '.branding.primaryColor'
done
```

**Expected Output:**
```
Testing dashen...
"#1a56db"  (Blue)
Testing abyssinia...
"#dc2626"  (Red)
Testing awash...
"#059669"  (Green)
Testing cbe...
"#f59e0b"  (Orange)
Testing amhara...
"#0ea5e9"  (Sky Blue)
Testing zemen...
"#7c3aed"  (Purple)
Testing tsedey...
"#ec4899"  (Pink)
Testing nib...
"#10b981"  (Emerald)
```

---

## 📊 **Demo Scenarios**

### **Scenario 1: Multi-Bank Chatbot**
```bash
# Dashen Bank (Blue)
curl -X POST http://localhost:8000/api/chat \
  -H "X-Bank-Id: dashen" \
  -H "Content-Type: application/json" \
  -d '{"sessionId": "demo1", "message": "What mobile banking do you offer?"}'

# Zemen Bank (Purple)
curl -X POST http://localhost:8000/api/chat \
  -H "X-Bank-Id: zemen" \
  -H "Content-Type: application/json" \
  -d '{"sessionId": "demo2", "message": "What mobile banking do you offer?"}'
```

### **Scenario 2: Banking Intelligence**
```bash
# Dashen Dashboard
curl -X POST http://localhost:8000/api/intelligence/dashboard \
  -H "Content-Type: application/json" \
  -d '{"bankId": "dashen", "timeRange": "30d"}'

# Predictive Analytics
curl -X POST http://localhost:8000/api/intelligence/predict \
  -H "Content-Type: application/json" \
  -d '{"metricName": "deposit_growth", "horizonDays": 30, "bankId": "dashen"}'
```

### **Scenario 3: Fraud Detection**
```bash
curl -X POST http://localhost:8000/api/fraud/monitor \
  -H "Content-Type: application/json" \
  -d '{
    "events": [{
      "eventId": "demo-1",
      "customerId": "cust-123",
      "timestamp": "2026-08-18T22:00:00Z",
      "amount": 150000,
      "currency": "ETB",
      "channel": "atm",
      "eventType": "withdrawal"
    }],
    "bankId": "dashen"
  }'
```

---

## 🔧 **Troubleshooting**

### **Container won't start?**
```bash
# Check logs
docker-compose logs fraudshield-api

# Common issue: Missing API key
# Solution: Check your .env file has GEMINI_API_KEY set
```

### **Port 8000 already in use?**
```bash
# Change port in docker-compose.yml
ports:
  - "8001:8000"  # Use 8001 instead

# Then access at http://localhost:8001
```

### **Code changes not reflecting?**
```bash
# Rebuild the container
docker-compose up --build

# Or if running in background
docker-compose down
docker-compose up -d --build
```

### **Reset everything?**
```bash
# Stop and remove containers
docker-compose down

# Remove volumes (clears ChromaDB data)
docker-compose down -v

# Start fresh
docker-compose up --build
```

---

## 📁 **What's Included**

### **Files Created:**
- ✅ `Dockerfile` - Container image definition
- ✅ `docker-compose.yml` - Multi-service orchestration
- ✅ `.dockerignore` - Exclude unnecessary files
- ✅ `env.example` - Environment variable template

### **Features:**
- ✅ **Hot reload** - Code changes apply automatically
- ✅ **Data persistence** - ChromaDB data saved in `./data`
- ✅ **Health checks** - Auto-restart if unhealthy
- ✅ **Easy setup** - Just `docker-compose up`

---

## 🚀 **Production Deployment**

For production, you'd want to:

1. **Remove `--reload`** from CMD in Dockerfile
2. **Use production WSGI server** (gunicorn + uvicorn workers)
3. **Add Nginx** reverse proxy
4. **Enable PostgreSQL** (uncomment in docker-compose.yml)
5. **Use secrets management** (not .env files)
6. **Add SSL/TLS** certificates

But for **demo purposes**, the current setup is perfect! ✨

---

## 🎯 **Demo Presentation Tips**

### **Before Demo:**
```bash
# Start containers in background
docker-compose up -d

# Wait for health check
sleep 10

# Verify it's running
curl http://localhost:8000/api/bank/list
```

### **During Demo:**
```bash
# Show logs in real-time (optional)
docker-compose logs -f fraudshield-api
```

### **After Demo:**
```bash
# Stop containers
docker-compose down

# Or keep running for next demo
docker-compose restart
```

---

## 📊 **Container Status**

### **Check if running:**
```bash
docker-compose ps
```

### **Check health:**
```bash
docker inspect fraudshield-demo | jq '.[0].State.Health'
```

### **Resource usage:**
```bash
docker stats fraudshield-demo
```

---

## ✅ **Quick Reference**

| Command | Purpose |
|---------|---------|
| `docker-compose up` | Start demo (foreground) |
| `docker-compose up -d` | Start demo (background) |
| `docker-compose down` | Stop demo |
| `docker-compose logs -f` | View logs |
| `docker-compose restart` | Restart demo |
| `docker-compose up --build` | Rebuild and start |

---

## 🎉 **Your Demo is Containerized!**

✅ **Easy to start** - One command  
✅ **Easy to stop** - One command  
✅ **Easy to reset** - One command  
✅ **Works anywhere** - Docker runs everywhere  
✅ **Professional** - Industry standard  

**Perfect for demos!** 🚀
