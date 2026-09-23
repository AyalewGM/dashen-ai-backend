# 🎨 Bank Trademark Themes & Branding

## Complete Bank List (8 Banks)

Your platform now supports **8 Ethiopian banks**, each with their unique trademark colors and branding:

---

## 🏦 **Bank Branding Matrix**

| # | Bank | Theme Color | Primary | Secondary | Accent | Tagline |
|---|------|-------------|---------|-----------|--------|---------|
| 1 | **Dashen Bank** | 🔵 Blue | `#1a56db` | `#93c5fd` | `#1e40af` | "Your trusted banking partner" |
| 2 | **Bank of Abyssinia** | 🔴 Red | `#dc2626` | `#fca5a5` | `#991b1b` | "Banking excellence since 1996" |
| 3 | **Awash Bank** | 🟢 Green | `#059669` | `#6ee7b7` | `#047857` | "Growing together with Ethiopia" |
| 4 | **Commercial Bank of Ethiopia** | 🟡 Orange | `#f59e0b` | `#fcd34d` | `#d97706` | "Ethiopia's largest bank" |
| 5 | **Amhara Bank** | 🔷 Sky Blue | `#0ea5e9` | `#7dd3fc` | `#0284c7` | "Banking for regional development" |
| 6 | **Zemen Bank** | 🟣 Purple | `#7c3aed` | `#c4b5fd` | `#5b21b6` | "Modern banking solutions" |
| 7 | **Tsedey Bank** | 🩷 Pink | `#ec4899` | `#f9a8d4` | `#be185d` | "Trusted financial partner" |
| 8 | **Nib International Bank** | 🟢 Emerald | `#10b981` | `#6ee7b7` | `#059669` | "International banking excellence" |

---

## 📊 **Visual Color Palette**

### **Dashen Bank** - Blue Theme
```css
Primary:   #1a56db  /* Deep Blue */
Secondary: #93c5fd  /* Light Blue */
Accent:    #1e40af  /* Dark Blue */
```
**Use Case**: Professional, trustworthy, established banking

---

### **Bank of Abyssinia** - Red Theme
```css
Primary:   #dc2626  /* Bold Red */
Secondary: #fca5a5  /* Light Red */
Accent:    #991b1b  /* Dark Red */
```
**Use Case**: Dynamic, energetic, innovative banking

---

### **Awash Bank** - Green Theme
```css
Primary:   #059669  /* Forest Green */
Secondary: #6ee7b7  /* Mint Green */
Accent:    #047857  /* Dark Green */
```
**Use Case**: Growth-focused, agricultural, sustainable banking

---

### **Commercial Bank of Ethiopia (CBE)** - Orange Theme
```css
Primary:   #f59e0b  /* Amber Orange */
Secondary: #fcd34d  /* Yellow */
Accent:    #d97706  /* Dark Orange */
```
**Use Case**: Government-backed, reliable, largest bank

---

### **Amhara Bank** - Sky Blue Theme
```css
Primary:   #0ea5e9  /* Sky Blue */
Secondary: #7dd3fc  /* Light Sky */
Accent:    #0284c7  /* Deep Sky */
```
**Use Case**: Regional focus, community banking, accessible

---

### **Zemen Bank** - Purple Theme
```css
Primary:   #7c3aed  /* Vibrant Purple */
Secondary: #c4b5fd  /* Lavender */
Accent:    #5b21b6  /* Deep Purple */
```
**Use Case**: Modern, tech-forward, innovative digital banking

---

### **Tsedey Bank** - Pink Theme
```css
Primary:   #ec4899  /* Hot Pink */
Secondary: #f9a8d4  /* Light Pink */
Accent:    #be185d  /* Deep Pink */
```
**Use Case**: Customer-centric, friendly, approachable banking

---

### **Nib International Bank** - Emerald Theme
```css
Primary:   #10b981  /* Emerald Green */
Secondary: #6ee7b7  /* Light Emerald */
Accent:    #059669  /* Deep Emerald */
```
**Use Case**: International banking, forex, trade finance

---

## 🎨 **CSS Implementation**

### **Dynamic Theme Switching**

```css
/* Define CSS variables */
:root {
  --primary-color: #1a56db;
  --secondary-color: #93c5fd;
  --accent-color: #1e40af;
}

/* Apply to components */
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

### **JavaScript Theme Switcher**

```javascript
async function applyBankTheme(bankId) {
  // Fetch bank config
  const response = await fetch(`/api/bank/info/${bankId}`);
  const config = await response.json();
  
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
  
  // Update logo
  document.querySelector('#bank-logo').src = config.branding.logoUrl;
  
  // Update title
  document.title = `${config.bankName} - FraudShield AI`;
}

// Example usage
applyBankTheme('dashen');    // Blue theme
applyBankTheme('zemen');     // Purple theme
applyBankTheme('tsedey');    // Pink theme
```

---

## 🔧 **Fraud Detection Thresholds**

Each bank has custom fraud detection rules:

| Bank | High Risk Threshold | Medium Risk Threshold |
|------|--------------------|-----------------------|
| **Amhara** | 90,000 ETB | 45,000 ETB |
| **Tsedey** | 95,000 ETB | 47,500 ETB |
| **Dashen** | 100,000 ETB | 50,000 ETB |
| **Zemen** | 110,000 ETB | 55,000 ETB |
| **Abyssinia** | 120,000 ETB | 60,000 ETB |
| **Nib** | 130,000 ETB | 65,000 ETB |
| **Awash** | 150,000 ETB | 75,000 ETB |
| **CBE** | 200,000 ETB | 100,000 ETB |

---

## 🌐 **Language Support**

| Bank | Supported Languages |
|------|---------------------|
| **Dashen** | English, Amharic, Oromo, Tigrinya, Somali |
| **Abyssinia** | English, Amharic, Oromo, Tigrinya |
| **Awash** | English, Amharic, Oromo |
| **CBE** | English, Amharic, Oromo, Tigrinya, Somali |
| **Amhara** | English, Amharic |
| **Zemen** | English, Amharic, Oromo |
| **Tsedey** | English, Amharic, Tigrinya |
| **Nib** | English, Amharic, Oromo |

---

## 🧪 **Testing Bank Themes**

```bash
# Test all bank themes
for bank in dashen abyssinia awash cbe amhara zemen tsedey nib; do
    echo "Testing $bank..."
    curl http://localhost:8000/api/bank/info/$bank | jq '.branding'
done
```

**Expected Output:**
```json
// Dashen - Blue
{
  "primaryColor": "#1a56db",
  "secondaryColor": "#93c5fd",
  "accentColor": "#1e40af"
}

// Zemen - Purple
{
  "primaryColor": "#7c3aed",
  "secondaryColor": "#c4b5fd",
  "accentColor": "#5b21b6"
}

// Tsedey - Pink
{
  "primaryColor": "#ec4899",
  "secondaryColor": "#f9a8d4",
  "accentColor": "#be185d"
}

// Nib - Emerald
{
  "primaryColor": "#10b981",
  "secondaryColor": "#6ee7b7",
  "accentColor": "#059669"
}
```

---

## 📱 **Demo Showcase**

### **Scenario 1: Traditional Banks**
- **Dashen** (Blue) → Professional, established
- **Abyssinia** (Red) → Dynamic, innovative
- **Awash** (Green) → Growth-focused

### **Scenario 2: Modern Banks**
- **Zemen** (Purple) → Tech-forward, digital-first
- **Nib** (Emerald) → International, sophisticated

### **Scenario 3: Regional/Community Banks**
- **Amhara** (Sky Blue) → Regional development
- **Tsedey** (Pink) → Customer-friendly, approachable

### **Scenario 4: Government Bank**
- **CBE** (Orange) → Largest, government-backed

---

## ✅ **Quick Reference**

### **Get Bank List**
```bash
curl http://localhost:8000/api/bank/list
```

### **Get Specific Bank Theme**
```bash
curl http://localhost:8000/api/bank/info/zemen
curl http://localhost:8000/api/bank/info/tsedey
curl http://localhost:8000/api/bank/info/amhara
curl http://localhost:8000/api/bank/info/nib
```

### **Test Chatbot with Bank Theme**
```bash
# Zemen Bank (Purple theme)
curl -X POST http://localhost:8000/api/chat \
  -H "X-Bank-Id: zemen" \
  -d '{"sessionId": "demo", "message": "What are your services?"}'

# Tsedey Bank (Pink theme)
curl -X POST http://localhost:8000/api/chat \
  -H "X-Bank-Id: tsedey" \
  -d '{"sessionId": "demo", "message": "Tell me about your bank"}'
```

---

## 🎯 **All 8 Banks Ready for Demo!**

✅ Each bank has unique trademark colors  
✅ Each bank has separate RAG knowledge base  
✅ Each bank has custom fraud detection rules  
✅ Each bank has multilingual support  
✅ Instant theme switching in UI  
✅ Production-ready white-label solution  

**Your platform now supports 8 Ethiopian banks from a single codebase!** 🚀
