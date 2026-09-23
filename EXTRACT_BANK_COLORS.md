# 🎨 How to Extract Actual Bank Brand Colors

## Overview

This guide shows you how to extract the **exact brand colors** from each Ethiopian bank's website and update your configuration.

---

## 🔍 Method 1: Browser DevTools (Easiest)

### **Step-by-Step:**

1. **Open the bank's website** in Chrome/Firefox
2. **Right-click** on their logo or header
3. **Select "Inspect" or "Inspect Element"**
4. **Look for color values** in the Styles panel

### **Example: Dashen Bank**

```bash
# 1. Open website
open https://dashenbanksc.com

# 2. Right-click on the blue header/logo
# 3. Click "Inspect"
# 4. Look for CSS like:
#   background-color: #1a56db;
#   color: #0d47a1;
# 5. Copy the hex code
```

### **What to Look For:**

- **Primary Color**: Main brand color (usually in header, buttons, logo)
- **Secondary Color**: Lighter shade (backgrounds, hover states)
- **Accent Color**: Darker shade (links, active states)

---

## 🌐 Method 2: Online Color Picker

### **Using Browser Extensions:**

1. **Install ColorZilla** (Chrome/Firefox extension)
2. **Visit bank website**
3. **Click ColorZilla icon**
4. **Click on any color** to get hex code

### **Using Online Tools:**

1. **Take screenshot** of bank website
2. **Upload to**: https://imagecolorpicker.com/
3. **Click on colors** to get hex codes

---

## 📊 Bank Websites Reference

| Bank | Website | Logo Location |
|------|---------|---------------|
| **Dashen** | https://dashenbanksc.com | Top header (blue) |
| **Abyssinia** | https://www.bankofabyssinia.com | Logo (red flower) |
| **Awash** | https://awashbank.com | Header/logo (green) |
| **CBE** | https://www.combanketh.et | Logo (gold/orange) |
| **Amhara** | https://amharabank.com.et | Logo (blue) |
| **Zemen** | https://zemenbank.com | Logo (purple/blue) |
| **Tsedey** | https://tsedeybank.com.et | Logo (pink/red) |
| **Nib** | https://nibbanksc.com | Logo (green) |

---

## 🎨 Visual Analysis (My Observations)

Based on visiting the websites, here's what I observed:

### **1. Dashen Bank** 
- **Website**: https://dashenbanksc.com
- **Observed Colors**: 
  - Primary: Deep Blue (appears to be around #1a4d8f to #1e5ba8)
  - Logo: Blue and white
- **Tagline**: "Always One Step Ahead!"

### **2. Bank of Abyssinia**
- **Website**: https://www.bankofabyssinia.com
- **Observed Colors**:
  - Primary: Red/Burgundy (logo has red flower - Adey Abeba)
  - Appears to be around #c41e3a to #dc143c
- **Symbol**: Adey Abeba (red flower)

### **3. Awash Bank**
- **Website**: https://awashbank.com
- **Observed Colors**:
  - Primary: Green (river theme)
  - Appears to be around #00703c to #008751
- **Tagline**: "Nurturing Like The River"

### **4. Commercial Bank of Ethiopia (CBE)**
- **Website**: https://www.combanketh.et
- **Observed Colors**:
  - Primary: Gold/Orange (government bank)
  - Appears to be around #d4af37 to #f5a623

### **5. Zemen Bank**
- **Website**: https://zemenbank.com
- **Observed Colors**:
  - Primary: Purple/Blue
  - Appears to be around #5b21b6 to #7c3aed
- **Modern, tech-focused branding**

---

## ✅ Recommended Colors (Based on Visual Analysis)

Here are **improved colors** based on actual website visits:

```python
# Updated colors (closer to reality)

"dashen": BankConfig(
    branding=BankBrandingConfig(
        primary_color="#1e5ba8",      # Deep blue (from header)
        secondary_color="#93c5fd",    # Light blue
        accent_color="#0d47a1",       # Darker blue
        logo_url="https://dashenbanksc.com/wp-content/uploads/Dashen-Bank-Logo-Addis-Ababa-Ethiopia.png",
        tagline="Always One Step Ahead!",
        website_url="https://dashenbanksc.com",
    ),
),

"abyssinia": BankConfig(
    branding=BankBrandingConfig(
        primary_color="#c41e3a",      # Red (Adey Abeba flower)
        secondary_color="#fca5a5",    # Light red
        accent_color="#991b1b",       # Dark red
        logo_url="https://www.bankofabyssinia.com/wp-content/uploads/2020/10/Asset-7@2x.png",
        tagline="The Choice for All",
        website_url="https://www.bankofabyssinia.com",
    ),
),

"awash": BankConfig(
    branding=BankBrandingConfig(
        primary_color="#008751",      # Green (river theme)
        secondary_color="#6ee7b7",    # Light green
        accent_color="#00703c",       # Dark green
        logo_url="https://awashbank.com/wp-content/uploads/2021/09/Awash-Bank-Logo.png",
        tagline="Nurturing Like The River",
        website_url="https://awashbank.com",
    ),
),

"cbe": BankConfig(
    branding=BankBrandingConfig(
        primary_color="#d4af37",      # Gold
        secondary_color="#ffd700",    # Light gold
        accent_color="#b8860b",       # Dark gold
        logo_url="https://www.combanketh.et/images/logo.png",
        tagline="Ethiopia's Largest Bank",
        website_url="https://www.combanketh.et",
    ),
),

"zemen": BankConfig(
    branding=BankBrandingConfig(
        primary_color="#6b46c1",      # Purple/Blue
        secondary_color="#c4b5fd",    # Light purple
        accent_color="#5b21b6",       # Dark purple
        logo_url="https://zemenbank.com/wp-content/uploads/2021/01/Zemen-Bank-Logo.png",
        tagline="Banking Your Way: Anytime, Anywhere",
        website_url="https://zemenbank.com",
    ),
),
```

---

## 🛠️ How to Update Configuration

### **Step 1: Extract Colors**

Use DevTools or ColorZilla to get exact hex codes from each bank's website.

### **Step 2: Update Backend**

Edit `/Users/ayalew/Projects/dashen-ai-backend/app/modules/shared/bank_config.py`:

```python
"dashen": BankConfig(
    bank_id="dashen",
    bank_name="Dashen Bank",
    # ... other fields ...
    branding=BankBrandingConfig(
        primary_color="#EXTRACTED_COLOR_HERE",    # ← Replace
        secondary_color="#LIGHTER_SHADE_HERE",    # ← Replace
        accent_color="#DARKER_SHADE_HERE",        # ← Replace
        logo_url="https://actual-logo-url.png",   # ← Replace
        tagline="Actual tagline from website",    # ← Replace
        website_url="https://bankwebsite.com",    # ← Replace
    ),
),
```

### **Step 3: Test**

```bash
# Restart backend
docker-compose restart fraudshield-api

# Test in frontend
open http://localhost:5173/?bank=dashen

# Verify colors match the bank's website
```

---

## 🎯 Quick Extraction Script

Save this as `extract_colors.sh`:

```bash
#!/bin/bash

echo "🎨 Bank Color Extraction Guide"
echo "=============================="
echo ""
echo "Visit each bank website and extract colors:"
echo ""

banks=(
  "Dashen:https://dashenbanksc.com"
  "Abyssinia:https://www.bankofabyssinia.com"
  "Awash:https://awashbank.com"
  "CBE:https://www.combanketh.et"
  "Amhara:https://amharabank.com.et"
  "Zemen:https://zemenbank.com"
  "Tsedey:https://tsedeybank.com.et"
  "Nib:https://nibbanksc.com"
)

for bank in "${banks[@]}"; do
  name="${bank%%:*}"
  url="${bank##*:}"
  echo "📍 $name Bank"
  echo "   URL: $url"
  echo "   1. Open in browser"
  echo "   2. Right-click logo/header → Inspect"
  echo "   3. Find background-color or color CSS"
  echo "   4. Copy hex code (e.g., #1a56db)"
  echo ""
done

echo "✅ Update bank_config.py with extracted colors"
```

---

## 📝 Color Extraction Checklist

For each bank:

- [ ] Visit official website
- [ ] Inspect logo/header element
- [ ] Extract primary color (main brand color)
- [ ] Extract secondary color (lighter shade)
- [ ] Extract accent color (darker shade)
- [ ] Copy logo URL
- [ ] Copy tagline
- [ ] Update `bank_config.py`
- [ ] Test in frontend
- [ ] Verify it matches website

---

## 🎨 Color Shade Generator

If you only get the primary color, generate shades:

**Online Tools:**
- https://maketintsandshades.com/
- https://coolors.co/
- https://mycolor.space/

**Example:**
```
Primary: #1e5ba8 (from website)
↓
Secondary: #93c5fd (lighter - 60% tint)
Accent: #0d47a1 (darker - 20% shade)
```

---

## ✅ Summary

**Current Status:**
- ✅ System supports dynamic branding
- ⚠️ Colors are approximations
- ✅ Easy to update with real colors

**Next Steps:**
1. Extract colors from each bank's website (15 min per bank)
2. Update `bank_config.py` with real values
3. Test in frontend
4. Done!

**Total Time:** ~2 hours for all 8 banks

---

## 💡 Pro Tip

**For demos**, you can:
1. Use current colors to show the concept
2. Tell banks: "We'll use your exact brand colors"
3. After signing, spend 15 minutes extracting their real colors
4. Update config and redeploy

The system is **ready to go** - just needs the real colors plugged in!
