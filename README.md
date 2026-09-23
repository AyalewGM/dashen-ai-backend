# FraudShield AI Platform Backend (Modular Monolith)

## 🎯 **White-Label Multi-Bank Demo Platform**

This platform is a **production-ready white-label solution** that serves multiple Ethiopian banks from a **single codebase**. Each bank sees a fully customized experience with their own:

- ✅ **Branding** (colors, logos, taglines)
- ✅ **RAG Knowledge Base** (trained on their website)
- ✅ **Fraud Detection Rules** (custom thresholds)
- ✅ **KPIs and Analytics** (bank-specific data)
- ✅ **Multilingual Support** (English, Amharic, Oromo, Tigrinya, Somali)

### **Supported Banks (8 Total)**
- 🔵 **Dashen Bank** (Blue theme)
- 🔴 **Bank of Abyssinia** (Red theme)
- 🟢 **Awash Bank** (Green theme)
- 🟡 **Commercial Bank of Ethiopia** (Orange theme)
- 🔷 **Amhara Bank** (Sky Blue theme)
- 🟣 **Zemen Bank** (Purple theme)
- 🩷 **Tsedey Bank** (Pink theme)
- 🟢 **Nib International Bank** (Emerald theme)

### **Quick Start**

#### **🐳 Docker (Recommended for Demo)**
```bash
# 1. Setup environment
cp env.example .env
# Edit .env and add your GEMINI_API_KEY

# 2. Start demo
docker-compose up --build

# 3. Test it
curl http://localhost:8000/api/bank/list
```

#### **🐍 Python (Local Development)**
```bash
# Install dependencies
pip install -r requirements.txt

# Start server
uvicorn main:app --reload

# Test it
curl http://localhost:8000/api/bank/list
```

### **Documentation**
- 🐳 [`DOCKER_DEMO_GUIDE.md`](DOCKER_DEMO_GUIDE.md) - Docker setup for demos
- 🗄️ [`DATABASE_SETUP_GUIDE.md`](DATABASE_SETUP_GUIDE.md) - **Database setup with seed data**
- 📊 [`ANALYTICS_QA_GUIDE.md`](ANALYTICS_QA_GUIDE.md) - **Natural language analytics Q&A**
- 📘 [`WHITE_LABEL_DEMO_GUIDE.md`](WHITE_LABEL_DEMO_GUIDE.md) - Complete white-label demo guide
- 🎨 [`BANK_THEMES.md`](BANK_THEMES.md) - All 8 bank trademark themes & colors
- 🏗️ [`MULTI_BANK_ARCHITECTURE.md`](MULTI_BANK_ARCHITECTURE.md) - Architecture diagrams
- 🚀 [`GOOZOM_SOLUTIONS_IMPLEMENTATION.md`](GOOZOM_SOLUTIONS_IMPLEMENTATION.md) - AI solutions implementation
- 🤖 [`BANK_SPECIFIC_RAG.md`](BANK_SPECIFIC_RAG.md) - Bank-specific RAG details
- 📋 [`DEMO_QUICK_START.md`](DEMO_QUICK_START.md) - Quick demo guide

## Structure

- `main.py` – FastAPI app entrypoint, includes API routers.
- `app/api/` – HTTP layer only (routing, validation, serialization).
  - `conversation_api.py` – `/api/chat/*` endpoints.
  - `voice_ai_api.py` – `/api/voice/*` endpoints.
- `app/modules/` – Internal service-style modules.
  - `conversation/` – Text chatbot domain (models + service).
  - `voice_ai/` – Voice assistant + notifications (models + templates + service).
  - `shared/` – Cross-cutting concerns (config, logging, llm assistant, sessions).
- `tests/` – API-level tests for conversation and voice_ai.

## Adding a New Domain (e.g. Fraud Detection)

1. Create a new folder under `app/modules/`, e.g. `fraud/` with:
   - `__init__.py`
   - `models.py` – request/response/domain models.
   - `service.py` – business logic for the fraud domain.
2. Add a new API file under `app/api/`, e.g. `fraud_api.py` that:
   - Defines a FastAPI `APIRouter`.
   - Validates HTTP input, maps to `fraud.models` types.
   - Calls into `fraud.service` for all business logic.
   - Maps results back to HTTP responses.
3. Wire the new router in `main.py` (or `app/api/__init__.py`) using `include_router`.
4. Reuse shared infrastructure from `app/modules/shared` as needed (config, logging, llm assistant, sessions).

This keeps a **single deployable server** while organizing each domain as its own internal service-style module with clear boundaries.

## Insights Security Separation

Two separate namespaces are exposed:

- `/api/internal/insights/*`
  - Intended for internal staff (management/analytics).
  - Requires an **internal** token with RBAC roles.
  - Demo endpoints:
    - `GET /api/internal/insights/kpis`
      - Allowed roles: `ROLE_EXECUTIVE`, `ROLE_ANALYTICS`, `ROLE_FINANCE`, `ROLE_RISK`
    - `POST /api/internal/insights/query`
      - Allowed roles: `ROLE_EXECUTIVE`, `ROLE_ANALYTICS`

- `/api/customer/insights/*`
  - Intended for authenticated customers (my money dashboard).
  - Requires a **customer** token.
  - Customer scoping rule: the server derives `customerId` from the token and ignores any `customerId` provided by the client.
  - Demo endpoints:
    - `GET /api/customer/insights/summary`
    - `POST /api/customer/insights/query`

### Token claim contract

- Internal staff token:
  - `tokenType: "internal"`
  - `userId: string`
  - `roles: list[string]`

- Customer token:
  - `tokenType: "customer"`
  - `customerId: string`
  - `accountIds: optional list[string]`

### Audit logging

Insights endpoints call `app/modules/shared/audit.py:audit_log()` on:

- success
- denied
- error

## Insights + Ingestion (Postgres)

This server can run in:

- **Stub mode** (default): if `DATABASE_URL` is not set, insights endpoints return deterministic demo values.
- **Postgres mode**: if `DATABASE_URL` is set, the server bootstraps required tables on startup and insights queries read from Postgres.

### Required environment variables

- `DATABASE_URL` (Postgres connection string)
  - Example: `postgresql://postgres:postgres@localhost:5432/dashen_ai`
- `UPLOADS_DIR` (optional)
  - Defaults to `./data/uploads`

### Ingestion endpoints (internal only)

- `POST /api/internal/ingestion/upload`
  - RBAC roles: `ROLE_ANALYTICS` or `ROLE_EXECUTIVE`
  - `multipart/form-data`:
    - `file` (CSV)
    - `datasetType` = `customer` | `internal`
    - `datasetName` (string)
- `POST /api/internal/ingestion/seed-demo`
  - RBAC roles: `ROLE_ANALYTICS`
  - Seeds demo customers/transactions and internal KPI time series.
