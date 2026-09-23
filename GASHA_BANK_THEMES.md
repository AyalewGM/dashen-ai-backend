# ጋሻ (Gasha) - Bank-Specific Theming

Gasha fraud monitoring dashboard now dynamically adapts its colors based on the selected bank's branding.

## Bank Color Schemes

### 1. **Dashen Bank** (Default)
- **Primary Color**: `#1e5ba8` (Deep Blue)
- **Accent Color**: `#0d47a1` (Darker Blue)
- **Theme**: Professional blue gradient
- **Use Case**: Default theme, corporate and trustworthy

---

### 2. **Amhara Bank**
- **Primary Color**: `#025AA2` (Royal Blue)
- **Secondary Color**: `#FFCE03` (Golden Yellow)
- **Accent Color**: `#00A2AE` (Teal)
- **Theme**: Blue-yellow gradient with teal accents
- **Use Case**: Regional bank with vibrant, distinctive colors

---

### 3. **Tsehay Bank**
- **Primary Color**: `#2c5b36` (Forest Green)
- **Secondary Color**: `#000000` (Black)
- **Accent Color**: `#ffffff` (White)
- **Theme**: Green-black gradient, natural and grounded
- **Use Case**: "Sun" bank with earthy, reliable colors

---

### 4. **Zemen Bank**
- **Primary Color**: `#6b46c1` (Purple)
- **Accent Color**: `#5b21b6` (Deep Purple)
- **Theme**: Purple gradient, modern and innovative
- **Use Case**: Tech-forward bank with distinctive purple branding

---

### 5. **Tsedey Bank**
- **Primary Color**: `#d81b60` (Pink/Magenta)
- **Accent Color**: `#ad1457` (Deep Pink)
- **Theme**: Pink-magenta gradient, vibrant and approachable
- **Use Case**: Growing bank with bold, friendly colors

---

### 6. **Nib International Bank**
- **Primary Color**: `#f57c00` (Orange)
- **Accent Color**: `#e65100` (Deep Orange)
- **Theme**: Orange gradient, energetic and international
- **Use Case**: International bank with warm, dynamic colors

---

### 7. **Birhan Bank**
- **Primary Color**: `#2e7d32` (Green)
- **Accent Color**: `#1b5e20` (Dark Green)
- **Theme**: Green gradient, fresh and prosperous
- **Use Case**: "Light" bank with growth-oriented green colors

---

### 8. **Commercial Bank of Ethiopia (CBE)**
- **Primary Color**: `#1e40af` (Navy Blue)
- **Accent Color**: `#1e3a8a` (Deep Navy)
- **Theme**: Navy blue gradient, government-backed authority
- **Use Case**: Largest bank with authoritative, stable colors

---

## Where Colors Are Applied

### Dashboard Elements Using Bank Colors:

1. **Header Gradient**
   - Background: `linear-gradient(to right, primaryColor, accentColor)`
   - Applies to main dashboard header

2. **Loading Spinner**
   - Border color: `primaryColor`
   - Shows during data loading

3. **AI Accuracy Stat**
   - Text color: `primaryColor`
   - Highlights bank-specific performance

4. **Transaction Detail Modal**
   - Header gradient: `linear-gradient(to right, primaryColor, accentColor)`
   - "Create Case" button: `backgroundColor: primaryColor`

5. **Future Enhancements** (Planned)
   - Alert toast notifications
   - Pattern detection cards
   - Chart accent colors
   - Button hover states

---

## How It Works

### Frontend Implementation:
```typescript
const { bankConfig } = useBank();
const primaryColor = bankConfig.branding.primaryColor || '#dc2626';
const accentColor = bankConfig.branding.accentColor || '#ea580c';

// Apply to elements
<div style={{ background: `linear-gradient(to right, ${primaryColor}, ${accentColor})` }}>
```

### Backend Configuration:
```python
# app/modules/shared/bank_config.py
branding=BankBrandingConfig(
    primary_color="#1e5ba8",
    secondary_color="#93c5fd",
    accent_color="#0d47a1",
    logo_url="http://localhost:8000/static/logos/dashen.png",
)
```

---

## Demo Instructions

### To See Different Bank Themes:

1. **Switch Bank** using the bank selector in the top-right corner
2. **Navigate to Gasha** (`/fraudshield` route)
3. **Observe Color Changes**:
   - Header gradient changes to bank colors
   - AI Accuracy stat changes color
   - Loading spinner uses bank color
4. **Click Transaction** to see modal with bank-themed header
5. **Compare Banks** by switching between them

---

## Benefits

✅ **Brand Consistency** - Each bank sees their own colors  
✅ **White-Label Ready** - Easy to customize per bank  
✅ **Professional** - Matches bank's existing branding  
✅ **Scalable** - Add new banks by updating config  
✅ **Demo-Friendly** - Shows multi-tenant capability  

---

## Future Enhancements

### Planned Color Applications:
- [ ] Chart colors (risk distribution, fraud types)
- [ ] Alert toast notification colors
- [ ] Pattern detection card accents
- [ ] Button hover states
- [ ] Badge colors for severity levels
- [ ] Progress bar colors
- [ ] Icon colors throughout dashboard

### Advanced Theming:
- [ ] Dark mode support per bank
- [ ] Custom fonts per bank
- [ ] Logo-based color extraction
- [ ] Accessibility contrast checking
- [ ] Theme preview in bank selector

---

**Last Updated**: August 31, 2026  
**Version**: 1.0  
**Status**: ✅ Implemented and Tested
