# 🤖 AI Models Guide

## Current Configuration

Your FraudShield AI platform is configured to use **Google Gemini** as the primary AI model.

---

## 🎯 **Primary Model: Google Gemini**

### **Default Configuration:**
```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL_NAME=gemini-2.0-flash-exp
GEMINI_TEMPERATURE=0.2
```

### **Model Details:**

| Feature | Value |
|---------|-------|
| **Provider** | Google AI |
| **Model** | `gemini-2.0-flash-exp` (default) |
| **Alternative** | `gemini-2.5-pro` (in code default) |
| **Temperature** | 0.2 (low randomness, more consistent) |
| **API Key** | Required (from Google AI Studio) |

---

## 🔧 **Supported Models**

### **1. Google Gemini (Current)**

**Available Models:**
- ✅ `gemini-2.0-flash-exp` - **Fastest**, experimental, free tier
- ✅ `gemini-2.5-pro` - **Most capable**, production-ready
- ✅ `gemini-1.5-pro` - Stable, proven
- ✅ `gemini-1.5-flash` - Fast, cost-effective

**Recommended:**
```env
# For demos/development (fast, free)
GEMINI_MODEL_NAME=gemini-2.0-flash-exp

# For production (best quality)
GEMINI_MODEL_NAME=gemini-2.5-pro
```

**Get API Key:**
1. Visit: https://aistudio.google.com/apikey
2. Create new API key
3. Copy to `.env` file

**Pricing:**
- Free tier: 15 requests/minute
- Paid tier: Pay-as-you-go

---

### **2. OpenAI (Optional, Not Configured)**

**Available Models:**
- `gpt-4o` - Most capable
- `gpt-4o-mini` - Fast and cheap
- `gpt-3.5-turbo` - Legacy, cheap

**To Enable:**
```env
# Add to .env
OPENAI_API_KEY=sk-your_openai_key_here
```

**Note:** Code currently uses Gemini. To use OpenAI, you'd need to modify `llm_assistant.py`.

---

## 📊 **Model Comparison**

| Model | Speed | Quality | Cost | Best For |
|-------|-------|---------|------|----------|
| **gemini-2.0-flash-exp** | ⚡⚡⚡ | 🟢🟢 | 💰 Free | Demos, development |
| **gemini-2.5-pro** | ⚡⚡ | 🟢🟢🟢 | 💰💰 | Production |
| **gemini-1.5-flash** | ⚡⚡⚡ | 🟢🟢 | 💰 | High volume |
| **gpt-4o** | ⚡⚡ | 🟢🟢🟢 | 💰💰💰 | Premium quality |
| **gpt-4o-mini** | ⚡⚡⚡ | 🟢🟢 | 💰 | Cost-effective |

---

## 🎨 **What the AI Model Does**

### **1. Chatbot Conversations**
```python
# File: app/modules/conversation/service.py
# Uses Gemini for:
- Answering customer questions
- Multilingual support (5+ languages)
- RAG-based responses (bank-specific knowledge)
- Translation (cross-lingual queries)
```

### **2. Analytics Q&A**
```python
# File: app/modules/conversation/analytics_agent.py
# Uses Gemini for:
- Natural language analytics queries
- Formatting data into readable answers
- Multilingual analytics responses
```

### **3. Fraud Detection**
```python
# File: app/modules/fraud/service.py
# Uses Gemini for:
- Generating fraud explanations
- Risk assessment narratives
- Alert descriptions
```

### **4. Banking Intelligence**
```python
# File: app/modules/banking_intelligence/service.py
# Uses Gemini for:
- Decision support narratives
- Strategic recommendations
- Insight generation
```

---

## ⚙️ **Configuration Options**

### **Temperature Setting**

Controls randomness of responses:

```env
# Conservative (recommended for banking)
GEMINI_TEMPERATURE=0.2

# Balanced
GEMINI_TEMPERATURE=0.5

# Creative (not recommended for banking)
GEMINI_TEMPERATURE=0.9
```

**Recommendation:** Keep at `0.2` for consistent, reliable banking responses.

---

### **Model Selection**

```env
# Fast, experimental (good for demos)
GEMINI_MODEL_NAME=gemini-2.0-flash-exp

# Production-ready, high quality
GEMINI_MODEL_NAME=gemini-2.5-pro

# Stable, proven
GEMINI_MODEL_NAME=gemini-1.5-pro

# Fast, cost-effective
GEMINI_MODEL_NAME=gemini-1.5-flash
```

---

## 🚀 **Setup Instructions**

### **Step 1: Get Gemini API Key**

```bash
# 1. Visit Google AI Studio
open https://aistudio.google.com/apikey

# 2. Click "Create API Key"
# 3. Copy the key (starts with "AI...")
```

### **Step 2: Configure Environment**

```bash
# 1. Copy example file
cp env.example .env

# 2. Edit .env file
nano .env

# 3. Add your API key
GEMINI_API_KEY=AIza...your_key_here
GEMINI_MODEL_NAME=gemini-2.0-flash-exp
```

### **Step 3: Test**

```bash
# Start server
docker-compose up -d

# Test chatbot
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "test",
    "message": "Hello, what services do you offer?"
  }'
```

---

## 🔄 **Switching Models**

### **From Gemini to OpenAI**

Currently requires code changes. Here's how:

1. **Install OpenAI SDK:**
```bash
pip install openai
```

2. **Modify `llm_assistant.py`:**
```python
# Replace Gemini imports with:
import openai

# Update generate_reply() to use OpenAI API
```

3. **Add API key:**
```env
OPENAI_API_KEY=sk-your_key_here
```

---

### **Using Multiple Models**

You could configure different models for different tasks:

```python
# Example architecture:
- Chatbot: gemini-2.0-flash-exp (fast, cheap)
- Analytics: gemini-2.5-pro (high quality)
- Fraud: gemini-1.5-flash (balanced)
```

---

## 💰 **Cost Considerations**

### **Gemini Pricing (Approximate)**

| Model | Input | Output | Free Tier |
|-------|-------|--------|-----------|
| **gemini-2.0-flash-exp** | Free | Free | 15 req/min |
| **gemini-2.5-pro** | $0.00125/1K | $0.005/1K | 2 req/min |
| **gemini-1.5-flash** | $0.000075/1K | $0.0003/1K | 15 req/min |

### **Estimated Monthly Costs**

**Scenario: 1,000 users, 10 queries/day**

```
Total queries: 1,000 × 10 × 30 = 300,000/month

Using gemini-2.0-flash-exp:
- Cost: $0 (free tier)

Using gemini-2.5-pro:
- Input tokens: ~150M tokens
- Output tokens: ~50M tokens
- Cost: ~$437/month

Using gemini-1.5-flash:
- Cost: ~$26/month
```

**Recommendation:** Start with `gemini-2.0-flash-exp` (free), upgrade to `gemini-1.5-flash` for production.

---

## 🌍 **Multilingual Support**

The AI model handles **5+ Ethiopian languages**:

```python
Supported Languages:
- English (en)
- Amharic (am)
- Afan Oromo (om)
- Tigrinya (ti)
- Somali (so)
- Sidama (sid)
```

**How it works:**
1. User asks in Amharic
2. System translates to English (for RAG)
3. Retrieves relevant info
4. Generates answer in English
5. Translates back to Amharic
6. Returns to user

**Model Requirements:**
- Must support multilingual translation
- Gemini 2.0+ recommended (best multilingual)

---

## 🔒 **Security & Best Practices**

### **API Key Security**

```bash
# ✅ DO: Use environment variables
GEMINI_API_KEY=AIza...

# ❌ DON'T: Hardcode in code
api_key = "AIza..."  # NEVER DO THIS

# ✅ DO: Add .env to .gitignore
echo ".env" >> .gitignore

# ✅ DO: Use different keys for dev/prod
# .env.development
GEMINI_API_KEY=AIza...dev_key

# .env.production
GEMINI_API_KEY=AIza...prod_key
```

### **Rate Limiting**

```python
# Implement rate limiting to avoid quota exhaustion
# Example: Max 100 requests per user per hour
```

### **Error Handling**

Current implementation includes:
- ✅ Fallback messages if API fails
- ✅ Graceful degradation
- ✅ Error logging
- ✅ Retry logic (via asyncio)

---

## 📊 **Monitoring & Optimization**

### **Track Model Performance**

```python
# Metrics to monitor:
- Response latency
- Token usage
- Error rate
- User satisfaction
- Cost per query
```

### **Optimize Costs**

```python
# Strategies:
1. Cache common responses
2. Use semantic caching (already implemented)
3. Batch similar queries
4. Use cheaper models for simple tasks
5. Implement response length limits
```

---

## 🎯 **Recommendations**

### **For Development/Demos:**
```env
GEMINI_MODEL_NAME=gemini-2.0-flash-exp
GEMINI_TEMPERATURE=0.2
```
- ✅ Free
- ✅ Fast
- ✅ Good enough for demos

### **For Production:**
```env
GEMINI_MODEL_NAME=gemini-1.5-flash
GEMINI_TEMPERATURE=0.2
```
- ✅ Cost-effective ($26/month for 300K queries)
- ✅ Reliable
- ✅ Good quality

### **For Premium Quality:**
```env
GEMINI_MODEL_NAME=gemini-2.5-pro
GEMINI_TEMPERATURE=0.2
```
- ✅ Best quality
- ✅ Most capable
- ⚠️ Higher cost ($437/month for 300K queries)

---

## ✅ **Summary**

**Current Setup:**
- ✅ **Model**: Google Gemini
- ✅ **Default**: `gemini-2.0-flash-exp` (free, fast)
- ✅ **Alternative**: `gemini-2.5-pro` (high quality)
- ✅ **Temperature**: 0.2 (consistent responses)
- ✅ **Features**: Multilingual, RAG, analytics, fraud detection

**What You Need:**
1. Gemini API key (free from Google AI Studio)
2. Add to `.env` file
3. Choose model based on needs
4. Monitor usage and costs

**Next Steps:**
1. Get API key: https://aistudio.google.com/apikey
2. Update `.env` file
3. Test with chatbot
4. Monitor performance
5. Optimize as needed

---

## 🔗 **Useful Links**

- **Get Gemini API Key**: https://aistudio.google.com/apikey
- **Gemini Pricing**: https://ai.google.dev/pricing
- **Gemini Models**: https://ai.google.dev/models/gemini
- **OpenAI Pricing**: https://openai.com/pricing

---

## 🎉 **You're Using:**

✅ **Google Gemini** - Fast, reliable, multilingual AI  
✅ **Free tier available** - Perfect for demos  
✅ **Production-ready** - Scalable to millions of users  
✅ **Ethiopian language support** - 5+ languages  
✅ **Already configured** - Just add API key!
