# White-Label Multi-Bank Demo Guide

## 🎯 **Challenge Solved**

You want to demo the same application to **multiple banks** (Dashen, Abyssinia, Awash, CBE) where each bank sees:
1. ✅ **Their own branding** (logo, colors, tagline)
2. ✅ **Their own data** (KPIs, metrics, insights)
3. ✅ **Their own chatbot** (trained on their website data)
4. ✅ **Their own fraud rules** (custom thresholds)

**Without building separate applications!**

---

## ✅ **What's Already Implemented**

### 1. **Bank-Specific Configuration**

Each bank has complete configuration in `app/modules/shared/bank_config.py`:

```python
BANK_CONFIGS = {
    "dashen": {
        "bank_name": "Dashen Bank",
        "branding": {
            "primary_color": "#1a56db",      # Blue
            "secondary_color": "#93c5fd",
            "accent_color": "#1e40af",
            "logo_url": "https://www.dashenbanksc.com/.../logo.png",
            "tagline": "Your trusted banking partner",
            "website_url": "https://www.dashenbanksc.com"
        },
        "fraud_rules": {
            "high_amount_threshold": 100_000,
            "medium_amount_threshold": 50_000
        },
        "chatbot_context": "You are a helpful assistant for Dashen Bank..."
    },
    "abyssinia": {
        "bank_name": "Bank of Abyssinia",
        "branding": {
            "primary_color": "#dc2626",      # Red
            "secondary_color": "#fca5a5",
            "accent_color": "#991b1b",
            "logo_url": "https://bankofabyssinia.com/.../logo.png",
            "tagline": "Banking excellence since 1996"
        },
        "fraud_rules": {
            "high_amount_threshold": 120_000,
            "medium_amount_threshold": 60_000
        }
    },
    "awash": {
        "branding": {
            "primary_color": "#059669",      # Green
            ...
        }
    },
    "cbe": {
        "branding": {
            "primary_color": "#f59e0b",      # Orange/Yellow
            ...
        }
    }
}
```

### 2. **Bank-Specific RAG (Chatbot Knowledge)**

Each bank has **separate RAG knowledge base** trained on their website:

**File**: `app/modules/shared/rag/loader.py`

```python
BANK_SEED_URLS = {
    "dashen": [
        "https://www.dashenbanksc.com/",
        "https://www.dashenbanksc.com/how-to-transfer-money-using-dashen-mobile-plus/",
        "https://www.dashenbanksc.com/frequently-asked-questions/",
        ...
    ],
    "abyssinia": [
        "https://bankofabyssinia.com/",
        "https://bankofabyssinia.com/services/",
        "https://bankofabyssinia.com/digital-banking/",
        ...
    ],
    "awash": [...],
    "cbe": [...]
}
```

**How it works:**
- Documents are scraped from each bank's website
- Stored in ChromaDB with `bank_id` metadata
- When chatbot queries, it **only retrieves documents for that bank**
- See `BANK_SPECIFIC_RAG.md` for technical details

### 3. **Bank-Specific Data in All APIs**

All APIs accept `bank_id` parameter or `X-Bank-Id` header:

```bash
# Intelligence Dashboard for Dashen
curl -X POST http://localhost:8000/api/intelligence/dashboard \
  -H "Content-Type: application/json" \
  -d '{"bankId": "dashen", "timeRange": "30d"}'

# Intelligence Dashboard for Abyssinia
curl -X POST http://localhost:8000/api/intelligence/dashboard \
  -H "Content-Type: application/json" \
  -d '{"bankId": "abyssinia", "timeRange": "30d"}'

# Chatbot for Awash
curl -X POST http://localhost:8000/api/chat \
  -H "X-Bank-Id: awash" \
  -d '{"sessionId": "test", "message": "What are your services?"}'
```

---

## 🚀 **How to Use for Demo**

### **Step 1: Get Bank List**

```bash
GET /api/bank/list
```

**Response:**
```json
{
  "banks": [
    {
      "bank_id": "dashen",
      "bank_name": "Dashen Bank",
      "bank_name_short": "Dashen"
    },
    {
      "bank_id": "abyssinia",
      "bank_name": "Bank of Abyssinia",
      "bank_name_short": "Abyssinia"
    },
    {
      "bank_id": "awash",
      "bank_name": "Awash Bank",
      "bank_name_short": "Awash"
    },
    {
      "bank_id": "cbe",
      "bank_name": "Commercial Bank of Ethiopia",
      "bank_name_short": "CBE"
    }
  ]
}
```

### **Step 2: Get Bank Branding Configuration**

```bash
GET /api/bank/info/{bank_id}
```

**Example for Dashen:**
```bash
curl http://localhost:8000/api/bank/info/dashen
```

**Response:**
```json
{
  "bankId": "dashen",
  "bankName": "Dashen Bank",
  "bankNameShort": "Dashen",
  "currency": "ETB",
  "languages": ["en", "am", "om", "ti", "so"],
  "branding": {
    "primaryColor": "#1a56db",
    "secondaryColor": "#93c5fd",
    "accentColor": "#1e40af",
    "logoUrl": "https://www.dashenbanksc.com/wp-content/uploads/2021/01/logo.png",
    "faviconUrl": null,
    "tagline": "Your trusted banking partner",
    "websiteUrl": "https://www.dashenbanksc.com"
  }
}
```

**Example for Abyssinia:**
```bash
curl http://localhost:8000/api/bank/info/abyssinia
```

**Response:**
```json
{
  "bankId": "abyssinia",
  "bankName": "Bank of Abyssinia",
  "branding": {
    "primaryColor": "#dc2626",
    "secondaryColor": "#fca5a5",
    "accentColor": "#991b1b",
    "logoUrl": "https://bankofabyssinia.com/wp-content/uploads/2021/03/logo.png",
    "tagline": "Banking excellence since 1996"
  }
}
```

### **Step 3: Apply Branding in Frontend**

In your React/Vue/Angular frontend:

```typescript
// 1. Fetch bank config
const bankId = "dashen"; // or from dropdown/URL param
const response = await fetch(`/api/bank/info/${bankId}`);
const config = await response.json();

// 2. Apply branding dynamically
document.documentElement.style.setProperty('--primary-color', config.branding.primaryColor);
document.documentElement.style.setProperty('--secondary-color', config.branding.secondaryColor);
document.documentElement.style.setProperty('--accent-color', config.branding.accentColor);

// 3. Update logo
document.querySelector('#bank-logo').src = config.branding.logoUrl;

// 4. Update title
document.title = `${config.bankName} - FraudShield AI`;

// 5. Store bank_id for API calls
localStorage.setItem('bank_id', config.bankId);
```

### **Step 4: Use Bank ID in All API Calls**

```typescript
// Example: Chat API
const bankId = localStorage.getItem('bank_id');
await fetch('/api/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-Bank-Id': bankId  // ← Pass bank ID
  },
  body: JSON.stringify({
    sessionId: 'session-123',
    message: 'What are your loan rates?'
  })
});

// Example: Intelligence Dashboard
await fetch('/api/intelligence/dashboard', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    bankId: bankId,  // ← Pass bank ID
    timeRange: '30d'
  })
});

// Example: Fraud Monitoring
await fetch('/api/fraud/monitor', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    events: [...],
    bankId: bankId  // ← Pass bank ID
  })
});
```

---

## 🎨 **Frontend Implementation Example**

### **React Component with Bank Switcher**

```tsx
import { useState, useEffect } from 'react';

function BankSwitcher() {
  const [banks, setBanks] = useState([]);
  const [selectedBank, setSelectedBank] = useState('dashen');
  const [branding, setBranding] = useState(null);

  useEffect(() => {
    // Load bank list
    fetch('/api/bank/list')
      .then(res => res.json())
      .then(data => setBanks(data.banks));
  }, []);

  useEffect(() => {
    // Load bank branding when selection changes
    fetch(`/api/bank/info/${selectedBank}`)
      .then(res => res.json())
      .then(config => {
        setBranding(config.branding);
        
        // Apply CSS variables
        document.documentElement.style.setProperty(
          '--primary-color', 
          config.branding.primaryColor
        );
        document.documentElement.style.setProperty(
          '--secondary-color', 
          config.branding.secondaryColor
        );
        document.documentElement.style.setProperty(
          '--accent-color', 
          config.branding.accentColor
        );
        
        // Store for API calls
        localStorage.setItem('bank_id', config.bankId);
      });
  }, [selectedBank]);

  return (
    <div className="bank-switcher">
      <select 
        value={selectedBank} 
        onChange={(e) => setSelectedBank(e.target.value)}
      >
        {banks.map(bank => (
          <option key={bank.bank_id} value={bank.bank_id}>
            {bank.bank_name}
          </option>
        ))}
      </select>
      
      {branding && (
        <div className="bank-header">
          <img src={branding.logoUrl} alt="Bank Logo" />
          <p>{branding.tagline}</p>
        </div>
      )}
    </div>
  );
}
```

### **CSS Variables**

```css
:root {
  --primary-color: #1a56db;
  --secondary-color: #93c5fd;
  --accent-color: #1e40af;
}

.btn-primary {
  background-color: var(--primary-color);
}

.card-header {
  background-color: var(--secondary-color);
}

.link {
  color: var(--accent-color);
}
```

---

## 📊 **What Each Bank Sees**

### **Dashen Bank Demo**
- **Colors**: Blue theme (#1a56db)
- **Logo**: Dashen Bank logo
- **Chatbot**: Answers about Dashen services, Dashen Mobile Plus, etc.
- **Data**: Dashen-specific KPIs and metrics
- **Fraud Rules**: 100K ETB high threshold

### **Bank of Abyssinia Demo**
- **Colors**: Red theme (#dc2626)
- **Logo**: Abyssinia logo
- **Chatbot**: Answers about Abyssinia services, digital banking, etc.
- **Data**: Abyssinia-specific KPIs and metrics
- **Fraud Rules**: 120K ETB high threshold

### **Awash Bank Demo**
- **Colors**: Green theme (#059669)
- **Logo**: Awash logo
- **Chatbot**: Answers about Awash services, agricultural banking, etc.
- **Data**: Awash-specific KPIs and metrics
- **Fraud Rules**: 150K ETB high threshold

### **CBE Demo**
- **Colors**: Orange/Yellow theme (#f59e0b)
- **Logo**: CBE logo
- **Chatbot**: Answers about CBE services, government banking, etc.
- **Data**: CBE-specific KPIs and metrics
- **Fraud Rules**: 200K ETB high threshold

---

## 🔧 **Adding a New Bank**

To add a new bank (e.g., "Nib Bank"):

### 1. Add to `bank_config.py`:

```python
"nib": BankConfig(
    bank_id="nib",
    bank_name="Nib International Bank",
    bank_name_short="Nib",
    currency="ETB",
    languages=["en", "am"],
    fraud_rules=FraudRulesConfig(
        high_amount_threshold=110_000,
        medium_amount_threshold=55_000,
    ),
    branding=BankBrandingConfig(
        primary_color="#7c3aed",  # Purple
        secondary_color="#c4b5fd",
        accent_color="#5b21b6",
        logo_url="https://nibbanksc.com/logo.png",
        tagline="International banking excellence",
        website_url="https://nibbanksc.com",
    ),
    chatbot_context="You are a helpful assistant for Nib Bank customers...",
),
```

### 2. Add RAG URLs in `loader.py`:

```python
BANK_SEED_URLS = {
    # ... existing banks
    "nib": [
        "https://nibbanksc.com/",
        "https://nibbanksc.com/services/",
        "https://nibbanksc.com/about/",
    ],
}
```

### 3. That's it! 🎉

The new bank will automatically:
- ✅ Appear in `/api/bank/list`
- ✅ Have its own branding via `/api/bank/info/nib`
- ✅ Have its own RAG knowledge base
- ✅ Show bank-specific data in all APIs

---

## 🧪 **Testing Multi-Bank Demo**

```bash
# Start backend
uvicorn main:app --reload

# Test each bank's branding
curl http://localhost:8000/api/bank/info/dashen
curl http://localhost:8000/api/bank/info/abyssinia
curl http://localhost:8000/api/bank/info/awash
curl http://localhost:8000/api/bank/info/cbe

# Test each bank's chatbot
curl -X POST http://localhost:8000/api/chat \
  -H "X-Bank-Id: dashen" \
  -H "Content-Type: application/json" \
  -d '{"sessionId": "test", "message": "What are your services?"}'

curl -X POST http://localhost:8000/api/chat \
  -H "X-Bank-Id: abyssinia" \
  -H "Content-Type: application/json" \
  -d '{"sessionId": "test", "message": "What are your services?"}'

# Test each bank's intelligence dashboard
curl -X POST http://localhost:8000/api/intelligence/dashboard \
  -H "Content-Type: application/json" \
  -d '{"bankId": "dashen", "timeRange": "30d"}'

curl -X POST http://localhost:8000/api/intelligence/dashboard \
  -H "Content-Type: application/json" \
  -d '{"bankId": "awash", "timeRange": "30d"}'
```

---

## 🎯 **Demo Presentation Flow**

### **For Dashen Bank:**
1. Open app with `?bank=dashen` URL parameter
2. Show **blue theme** with Dashen logo
3. Chat: "What are your mobile banking features?" → Gets Dashen-specific answers
4. Show dashboard with Dashen KPIs
5. Run fraud detection with Dashen thresholds

### **Switch to Abyssinia:**
1. Change dropdown to "Bank of Abyssinia"
2. Watch UI **instantly change to red theme** with Abyssinia logo
3. Chat: "What are your services?" → Gets Abyssinia-specific answers
4. Show dashboard with Abyssinia KPIs
5. Run fraud detection with Abyssinia thresholds

**Each bank thinks the app was built specifically for them!** 🎭

---

## 📝 **Summary**

✅ **Single codebase** serves all banks  
✅ **Bank-specific branding** (colors, logos, taglines)  
✅ **Bank-specific chatbot** (trained on their website)  
✅ **Bank-specific data** (KPIs, metrics, insights)  
✅ **Bank-specific fraud rules** (custom thresholds)  
✅ **Easy to add new banks** (just config, no code changes)  
✅ **Production-ready** white-label solution  

**You can now demo to any Ethiopian bank with confidence!** 🚀
