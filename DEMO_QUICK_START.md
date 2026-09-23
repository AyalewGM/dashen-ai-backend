# FraudShield Multi-Bank Demo - Quick Start

## 🎯 What's New

Your FraudShield platform now supports **multiple banks** with:
- ✅ Bank-specific branding (logos, colors, names)
- ✅ Custom fraud detection thresholds per bank
- ✅ Bank-specific chatbot context and responses
- ✅ Easy switching between banks for demos
- ✅ URL-based bank selection

## 🚀 Demo in 3 Steps

### 1. Start Backend
```bash
cd /Users/ayalew/Projects/dashen-ai-backend
uvicorn main:app --reload
```

### 2. Start Frontend
```bash
cd /Users/ayalew/Projects/dashen-ai-frontend
npm install  # First time only
npm run dev
```

### 3. Open Browser

**For Dashen Bank Demo:**
```
http://localhost:5173/?bank=dashen
```

**For Bank of Abyssinia Demo:**
```
http://localhost:5173/?bank=abyssinia
```

**For Awash Bank Demo:**
```
http://localhost:5173/?bank=awash
```

**For Commercial Bank of Ethiopia Demo:**
```
http://localhost:5173/?bank=cbe
```

## 🎨 What Changes Per Bank

### Dashboard
- **Title**: Shows "{Bank Name} AI Platform"
- **Branding**: Bank-specific colors and taglines

### Chatbot
- **Context**: Knows about the specific bank
- **Responses**: Mentions the bank name naturally
- **Knowledge Base**: Retrieves information ONLY from that bank's documents
- **Example**: "Welcome to Awash Bank" vs "Welcome to Dashen Bank"
- **RAG**: Each bank has its own web pages indexed (Dashen from dashenbanksc.com, Abyssinia from bankofabyssinia.com, etc.)

### FraudShield
- **Thresholds**: Different risk levels per bank
  - Dashen: High risk at 100K ETB
  - Abyssinia: High risk at 120K ETB
  - Awash: High risk at 150K ETB
  - CBE: High risk at 200K ETB

## 🔄 Switching Banks During Demo

**Method 1: Use Bank Selector**
- Look for the bank dropdown in the top navigation
- Click and select a different bank
- Page reloads with new bank context

**Method 2: Change URL**
- Update `?bank=<bank_id>` in the URL
- Refresh the page

**Method 3: localStorage**
- Selection persists across page reloads
- Clear with: `localStorage.removeItem('selectedBankId')`

## 📊 Demo Script Example

### Opening
> "Today I'll show you FraudShield AI, our multi-bank fraud detection platform. Let me start with **Dashen Bank**..."

### Show Branding
> "Notice the dashboard says 'Dashen Bank AI Platform' - everything is branded for Dashen."

### Test Chatbot
> "Let me ask the chatbot: 'What services do you offer?'"
>
> *Bot responds with Dashen-specific context*

### Switch Banks
> "Now let me show you how easy it is to adapt this for another bank. I'll switch to **Bank of Abyssinia**..."
>
> *Use bank selector or change URL to `?bank=abyssinia`*

### Show Differences
> "See how the title changed? The chatbot now knows it's Bank of Abyssinia. Let me ask the same question..."
>
> *Bot responds with Abyssinia-specific context*

### Test FraudShield
> "The fraud detection rules are also customized. Abyssinia has a higher threshold of 120K ETB compared to Dashen's 100K ETB."

### Test Bank-Specific Knowledge
> "Let me ask about services: 'What mobile banking features do you offer?'"
>
> *Bot responds with Dashen-specific services*
>
> "Now let me switch to Awash Bank and ask the same question..."
>
> *Switch to Awash, ask same question*
>
> *Bot responds with Awash-specific services - completely different answer!*
>
> "Notice how the chatbot retrieved information from different sources? Each bank's knowledge base is completely separate."

### Closing
> "This same platform can be deployed for any bank with just configuration changes - no code modifications needed. The RAG system automatically indexes each bank's website and keeps the knowledge bases separate."

## 🎯 Key Demo Points

1. **No Code Changes**: Switching banks is configuration-only
2. **Instant Branding**: Logo, colors, names update automatically
3. **Smart Chatbot**: Knows which bank it's representing
4. **Separate Knowledge Bases**: Each bank's RAG retrieves only from their documents
5. **Custom Rules**: Each bank can have different fraud thresholds
6. **Easy Deployment**: Same codebase, multiple banks

## 🏦 Available Banks

| Bank | ID | Color | Threshold |
|------|-----|-------|-----------|
| Dashen Bank | `dashen` | Blue | 100K ETB |
| Bank of Abyssinia | `abyssinia` | Red | 120K ETB |
| Awash Bank | `awash` | Green | 150K ETB |
| Commercial Bank of Ethiopia | `cbe` | Orange | 200K ETB |

## 🔧 Adding Your Bank

Edit `app/modules/shared/bank_config.py` and add:

```python
"your_bank": BankConfig(
    bank_id="your_bank",
    bank_name="Your Bank Name",
    bank_name_short="YourBank",
    currency="ETB",
    fraud_rules=FraudRulesConfig(
        high_amount_threshold=100_000,
        medium_amount_threshold=50_000,
    ),
    branding=BankBrandingConfig(
        primary_color="#yourcolor",
        tagline="Your tagline",
    ),
    chatbot_context="Your bank description...",
)
```

Then access: `http://localhost:5173/?bank=your_bank`

## 📝 Notes

- **TypeScript Errors**: Ignore IDE errors until you run `npm install` in frontend
- **Backend Port**: Default is 8000, change in `main.py` if needed
- **Frontend Port**: Default is 5173 (Vite), change in `vite.config.ts` if needed
- **API Key**: Set `GEMINI_API_KEY` in `.env` for chatbot to work
- **First Chat Delay**: First chatbot request per bank may take 10-30 seconds while it indexes that bank's website. Subsequent requests are instant. See `BANK_SPECIFIC_RAG.md` for pre-indexing options.

## 🆘 Troubleshooting

**Bank not loading?**
```bash
# Check backend
curl http://localhost:8000/api/bank/list

# Should return list of banks
```

**Chatbot not responding?**
- Check `GEMINI_API_KEY` is set in backend `.env`
- Check backend console for errors

**Frontend not starting?**
```bash
cd /Users/ayalew/Projects/dashen-ai-frontend
npm install
npm run dev
```

## 📚 More Info

See `MULTI_BANK_SETUP.md` for detailed technical documentation.

---

**Ready to demo!** 🎉
