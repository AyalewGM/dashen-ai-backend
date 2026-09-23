# Multi-Bank Configuration Guide

## Overview

FraudShield AI Platform now supports multiple banks with bank-specific branding, context, and fraud detection rules. This guide explains how to configure and demo the platform for different banks.

## Architecture

### Backend Changes

1. **Bank Configuration System** (`app/modules/shared/bank_config.py`)
   - Centralized bank configurations
   - Bank-specific fraud rules (thresholds, channels)
   - Chatbot context and branding
   - Currently configured banks: Dashen, Bank of Abyssinia, Awash Bank, CBE

2. **Auth Context** (`app/modules/shared/auth.py`)
   - Added `bank_id` field to `AuthContext`
   - Extracted from token payload with fallback to "dashen"
   - Backward compatible with existing tokens

3. **API Endpoints**
   - `GET /api/bank/info/{bank_id}` - Get bank configuration
   - `GET /api/bank/list` - List all available banks
   - Chat API accepts `X-Bank-Id` header for bank context

4. **LLM Integration** (`app/modules/shared/llm_assistant.py`)
   - Bank-specific system prompts
   - Dynamic bank name replacement in responses
   - Bank context injected into chatbot conversations

### Frontend Changes

1. **Bank Context** (`src/context/BankContext.tsx`)
   - Global bank configuration state
   - Loads bank config from API
   - Persists selection in localStorage
   - Supports URL parameter `?bank=<bank_id>`

2. **Bank Selector Component** (`src/components/common/BankSelector.tsx`)
   - Dropdown to switch between banks
   - Updates URL and reloads configuration
   - Visible in navigation for easy demo switching

3. **Dynamic Branding**
   - Dashboard title shows bank name
   - Chatbot uses bank-specific context
   - All API calls include bank ID

## Demo Usage

### Quick Start

1. **Start Backend**:
   ```bash
   cd /Users/ayalew/Projects/dashen-ai-backend
   uvicorn main:app --reload
   ```

2. **Start Frontend**:
   ```bash
   cd /Users/ayalew/Projects/dashen-ai-frontend
   npm run dev
   ```

3. **Access with Bank Parameter**:
   - Dashen Bank: `http://localhost:5173/?bank=dashen`
   - Bank of Abyssinia: `http://localhost:5173/?bank=abyssinia`
   - Awash Bank: `http://localhost:5173/?bank=awash`
   - CBE: `http://localhost:5173/?bank=cbe`

### Demo Flow

1. **Open browser** with bank-specific URL
2. **Dashboard** shows bank name in title
3. **Use Bank Selector** (top right) to switch banks
4. **Chat with bot** - responses are bank-specific
5. **Test FraudShield** - rules adapt to bank thresholds

## Adding a New Bank

### 1. Backend Configuration

Edit `app/modules/shared/bank_config.py`:

```python
BANK_CONFIGS["new_bank"] = BankConfig(
    bank_id="new_bank",
    bank_name="New Bank Name",
    bank_name_short="NewBank",
    currency="ETB",  # or other currency
    languages=["en", "am"],
    fraud_rules=FraudRulesConfig(
        high_amount_threshold=100_000,  # Customize
        medium_amount_threshold=50_000,
        risky_channels=["atm", "web"],
    ),
    branding=BankBrandingConfig(
        primary_color="#1a56db",  # Bank's brand color
        tagline="Your tagline here",
    ),
    chatbot_context="You are a helpful assistant for New Bank customers. [Bank description...]",
)
```

### 2. Test the Configuration

```bash
# Test bank info endpoint
curl http://localhost:8000/api/bank/info/new_bank

# Test bank list
curl http://localhost:8000/api/bank/list
```

### 3. Access Frontend

Navigate to: `http://localhost:5173/?bank=new_bank`

## Bank-Specific Features

### Fraud Detection Rules

Each bank has customizable:
- **High amount threshold**: Triggers high-risk alerts
- **Medium amount threshold**: Triggers medium-risk alerts
- **Risky channels**: Channels considered higher risk
- **Transaction timing windows**: For rapid transaction detection

Example:
```python
fraud_rules=FraudRulesConfig(
    high_amount_threshold=150_000,  # Awash Bank: higher threshold
    medium_amount_threshold=75_000,
    risky_channels=["atm", "web", "mobile"],  # More channels
)
```

### Chatbot Context

Each bank gets custom chatbot personality:

```python
chatbot_context="You are a helpful assistant for Awash Bank customers. Awash Bank is one of Ethiopia's oldest and most trusted private banks, providing a wide range of financial services with a focus on agricultural and business banking."
```

This context is injected into every conversation, making responses bank-specific.

### Branding

- **Primary Color**: Applied to UI elements
- **Logo URL**: (Optional) Bank logo
- **Tagline**: Displayed on dashboard

## Token Format (For Production)

When implementing authentication, include `bankId` in JWT tokens:

```json
{
  "tokenType": "customer",
  "customerId": "cust-123",
  "bankId": "abyssinia"
}
```

Or for internal users:

```json
{
  "tokenType": "internal",
  "userId": "user-456",
  "roles": ["ROLE_ANALYTICS"],
  "bankId": "awash"
}
```

## API Integration

### Chat API with Bank Context

```javascript
// Frontend example
const response = await axios.post(
  'http://localhost:8000/api/chat',
  {
    sessionId: 'session-123',
    message: 'What are your loan rates?'
  },
  {
    headers: {
      'X-Bank-Id': 'abyssinia'  // Bank-specific context
    }
  }
);
```

### Fraud Scoring with Bank Rules

```javascript
const response = await axios.post(
  'http://localhost:8000/api/fraud/score',
  {
    event: {
      eventId: 'evt-123',
      amount: 80000,
      currency: 'ETB',
      channel: 'atm',
      // ... other fields
    }
  },
  {
    headers: {
      'X-Bank-Id': 'awash'  // Uses Awash Bank's thresholds
    }
  }
);
```

## Current Bank Configurations

| Bank ID | Bank Name | Currency | High Threshold | Primary Color |
|---------|-----------|----------|----------------|---------------|
| `dashen` | Dashen Bank | ETB | 100,000 | #1a56db (Blue) |
| `abyssinia` | Bank of Abyssinia | ETB | 120,000 | #dc2626 (Red) |
| `awash` | Awash Bank | ETB | 150,000 | #059669 (Green) |
| `cbe` | Commercial Bank of Ethiopia | ETB | 200,000 | #f59e0b (Orange) |

## Troubleshooting

### Bank Not Loading
- Check backend is running: `http://localhost:8000/api/bank/list`
- Verify bank_id exists in `BANK_CONFIGS`
- Check browser console for errors

### Chatbot Not Using Bank Context
- Verify `X-Bank-Id` header is sent
- Check backend logs for bank_id extraction
- Ensure GEMINI_API_KEY is configured

### Fraud Rules Not Applied
- Confirm bank_id is passed to fraud API
- Check `fraud_rules` configuration for the bank
- Review backend logs for rule evaluation

## Next Steps

1. **Add Bank Logos**: Upload logos and update `logo_url` in config
2. **Customize Languages**: Add/remove languages per bank
3. **Refine Fraud Rules**: Adjust thresholds based on bank data
4. **Add Bank-Specific RAG**: Load bank-specific documents for chatbot
5. **Implement Multi-Tenancy**: Add database-level isolation for production

## Support

For questions or issues, contact the development team or refer to the main README.md.
