# MailOps AI

> **Enterprise Work-Intelligence, Grounded RAG & Action Graph Platform**  
> Transform unstructured emails, attachments, contracts, and invoices into an explainable, relational operational knowledge layer.

[![Backend Tests](https://img.shields.io/badge/pytest-70%2F70%20passed%20(100%25)-success?style=flat-square)](backend/tests/)
[![E2E Tests](https://img.shields.io/badge/E2E%20Tests-76%2F76%20passed%20(100%25)-brightgreen?style=flat-square)](tests/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react)](https://react.dev/)
[![pgvector](https://img.shields.io/badge/pgvector-0.7+-336791?style=flat-square&logo=postgresql)](https://github.com/pgvector/pgvector)
[![Docker](https://img.shields.io/badge/Docker-Compose%20Ready-2496ED?style=flat-square&logo=docker)](docker-compose.yml)
[![Theme](https://img.shields.io/badge/Theme-Black%2FCharcoal%2FRed-red?style=flat-square)](frontend/src/index.css)

---

## 📖 Documentation Quicklinks

* 📘 **[Comprehensive User Guide (USER_GUIDE.md)](USER_GUIDE.md)** — Step-by-step instructions for mailbox sync, AI extractions, reply copilot, document OCR, RAG search, action graphs, keyboard shortcuts, and executive digest exports.
* 📋 **[Interactive API Documentation (Swagger)](https://mailops-backend-67g3.onrender.com/docs)** — OpenAPI interactive REST endpoints.
* 🟢 **[Live Cloud Status & Health](https://mailops-backend-67g3.onrender.com/health)** — Real-time healthcheck endpoint.

---

## 🌟 Overview

Modern enterprise operations struggle with information fragmentation across email threads, customer escalations, supplier invoices, and legal contracts. Critical deliverables, decisions, commitments, deadlines, and dependencies are easily lost.

**MailOps AI** solves this by unifying mailbox ingestion with deep multi-layer AI intelligence:
- **Semantic Understanding:** Performs entity extraction, priority scoring, risk identification, and structured invoice parsing.
- **Relational Knowledge:** Models dependencies across email threads, tasks, documents, and stakeholders in an interactive **Action Graph** with BFS blocking-path traversal.
- **Grounded Retrieval (RAG):** Combines 768-dimensional vector embeddings with cross-encoder re-ranking for verifiable answers with clickable source citations.
- **Human-in-the-Loop Action:** Assists operators with context-aware reply drafts, inline ghost-text autocomplete (`Tab`), and 1-click Google Calendar scheduling.

---

## 🌐 Live Cloud Deployment

| Service | Live URL | Platform | Status |
|---|---|---|---|
| **Frontend Application** | [https://mailops-frontend.onrender.com](https://mailops-frontend.onrender.com) | Render (Static Site) | 🟢 Active |
| **Backend REST API** | [https://mailops-backend-67g3.onrender.com](https://mailops-backend-67g3.onrender.com) | Render (Docker Web Service) | 🟢 Active |
| **System Health Check** | [https://mailops-backend-67g3.onrender.com/health](https://mailops-backend-67g3.onrender.com/health) | Render | 🟢 Healthy |
| **Production Database** | Supabase Managed PostgreSQL 16 + `pgvector` | Supabase Cloud | 🟢 Connected |
| **24/7 Availability Monitor** | HTTP HEAD /health pings every 5m | UptimeRobot | 🟢 Active |

---

## 🏗️ System Architecture

```
                                  ┌───────────────────────────┐
                                  │   Desktop-Class 3-Pane    │
                                  │   React 18 + Vite SPA     │
                                  │  (Black / Charcoal / Red) │
                                  └─────────────┬─────────────┘
                                                │ REST / Cross-Site Session Cookies
                                                ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ FastAPI Application Core (Modular Monolith)                                            │
│                                                                                        │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────┐  │
│  │ Google OAuth 2.0 │  │ Ingestion & Sync │  │ AI Intelligence  │  │ Action Graph   │  │
│  │ PKCE & Sessions  │  │ Gmail REST & SSE │  │ Gemini 2.5 Flash │  │ BFS Dependency │  │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘  └────────────────┘  │
│                                                                                        │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────┐  │
│  │ Document OCR     │  │ Grounded RAG     │  │ AI Reply Copilot │  │ Distributed    │  │
│  │ PDF/DOCX/Tesseract│ │ pgvector + RRF   │  │ Ghost-Text Editor│  │ Worker Queue   │  │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘  └────────────────┘  │
└───────────────────────────────────────┬────────────────────────────────────────────────┘
                                        │ SQLAlchemy 2.0 / pgvector
                                        ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ PostgreSQL 16 + pgvector Database Storage                                              │
│                                                                                        │
│  • email_threads & messages    • extracted_actions & decisions    • vector_embeddings  │
│  • attachments & OCR data      • action_graph_nodes & edges       • reply_drafts       │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quickstart with Docker (Local)

Launch the full stack locally (PostgreSQL 16 with pgvector, FastAPI backend, and Nginx React frontend) with one command:

```bash
docker compose up -d
```

### Service Endpoints

| Service | Local URL | Description |
|---|---|---|
| **Frontend Application** | [http://localhost:3000](http://localhost:3000) | Desktop-class 3-pane client with dark theme |
| **Backend REST API** | [http://localhost:8000](http://localhost:8000) | FastAPI async REST endpoints |
| **Interactive API Docs** | [http://localhost:8000/docs](http://localhost:8000/docs) | OpenAPI / Swagger interactive documentation |
| **Prometheus Telemetry** | [http://localhost:8000/api/v1/webhooks/metrics](http://localhost:8000/api/v1/webhooks/metrics) | Real-time queue metrics and throughput |

> **⚡ Instant Demo Mode:** You do not need a live Google OAuth setup or Gemini API key to test the platform. Click **"⚡ Seed Demo"** on the login screen or dashboard to instantly load realistic enterprise escalation threads, multi-page invoices, and action graph dependencies.

---

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| **Backend Framework** | Python 3.12 / 3.14, FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2 |
| **Frontend Framework** | React 18, TypeScript 5.5, Vite, Tailwind CSS, Lucide Icons |
| **Database & Vector Engine** | PostgreSQL 16 with `pgvector` (768-d cosine distance search) |
| **AI / Embeddings** | Google Gemini 2.5 Flash (`google-genai`), `text-embedding-004`, Deterministic Fallback |
| **Document Processing** | PyPDF, python-docx, Pillow, pytesseract, pdf2image |
| **Notifications & Streaming**| Server-Sent Events (SSE), centralized non-blocking `ToastContext` |
| **Containerization & Web** | Docker, Docker Compose, Nginx Alpine |
| **Testing** | Pytest, pytest-asyncio, HTTPX TestClient (76/76 E2E, 70/70 Unit) |

---

## ⚙️ Environment Variables

Create a `.env` file in the project root (or copy from `.env.example`):

```bash
# Application Configuration
APP_NAME=EnterpriseAIMailOPs_MIPRO
APP_ENV=development
DEBUG=True
SECRET_KEY=dev_secret_key_change_in_production_min_64_bytes_secure_random_key_mailops
ENCRYPTION_KEY=4xW8Z3vK9uF2mP7qR1tY6bV5cN8jL0kH4gF2dS6aQ1w=

# Database (PostgreSQL + pgvector)
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=mailops_db
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/mailops_db

# Google OAuth 2.0 (Optional for offline demo)
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/google/callback

# AI Engine (Optional for offline demo)
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
AI_PROVIDER_TYPE=gemini

# Mailbox Synchronization
INITIAL_SYNC_LIMIT=50
ATTACHMENT_MAX_SIZE_BYTES=10485760

# Frontend URLs
VITE_API_BASE_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000
```

---

## 🧪 Testing & Verification

The test suite covers API endpoints, integration flows, document parsers, security isolation, multitenant audits, concurrency locks, and prompt injection defense:

```bash
# Run unit test suite
pytest backend/tests/unit -v

# Run full multi-tier E2E test suite (Tiers 1 - 5)
python tests/run_all_tests.py
```

### Test Suite Results: **100% Pass Rate**
* **Multi-Tier E2E Suites:** **76 / 76 Passed** across 5 tiers:
  * Tier 1 (Feature Coverage): 30/30
  * Tier 2 (Boundary Stress): 30/30
  * Tier 3 (Pairwise Interactions): 6/6
  * Tier 4 (Real-World Scenarios): 5/5
  * Tier 5 (Adversarial Rapid-Bombardment Stress): 5/5
* **Backend Unit Tests:** **70 / 70 Passed** with zero regressions.
* **Frontend Production Build:** Vite build compiled 59 modules cleanly in 1.25s with 0 errors.

---

## ☁️ Cloud Deployment (100% Free Tier Architecture)

```
[ Frontend: React / Vite ] ──> Render Static Site (Free, global CDN, custom domain)
            │
            ▼
[ Backend: FastAPI / Docker ] ──> Render Web Service (Free tier, auto-deploy from GitHub)
            │                         ▲
            │                         │ (Free 5-min ping keeps backend awake)
            ▼                   [ UptimeRobot ]
[ Database: PostgreSQL + pgvector ] ──> Supabase Cloud (Free tier, persistent 500 MB)
```

1. **Database (Supabase):** Provision a free project at [supabase.com](https://supabase.com). In Database → Extensions, enable `vector`. Copy your PostgreSQL connection URI.
2. **Backend (Render):** Create a **Web Service** pointing to your GitHub repo. Set Environment to `Docker` and configure `DATABASE_URL` from Supabase.
3. **Frontend (Render):** Create a **Static Site** pointing to `/frontend`. Build command: `npm install && npm run build`, publish directory: `dist`. Set `VITE_API_BASE_URL` to your Render backend URL.
4. **24/7 Uptime (UptimeRobot):** Set up a free HTTP monitor at [uptimerobot.com](https://uptimerobot.com) pinging `https://<your-backend>.onrender.com/health` every 5 minutes to prevent idle sleep.

---

## 📂 Repository Structure

```text
EnterpriseAIMailOPs_MIPRO/
├── backend/
│   ├── app/
│   │   ├── ai/            # Gemini & mock AI providers, prompt templates, reranker
│   │   ├── api/v1/        # FastAPI endpoint routers (auth, gmail, search, graph, reply)
│   │   ├── core/          # Configuration, security, crypto, distributed worker queue
│   │   ├── db/            # SQLAlchemy session management and base models
│   │   ├── integrations/  # Gmail and Google Calendar API clients
│   │   ├── models/        # Database models (User, Email, Vector, Graph, Audit)
│   │   ├── schemas/       # Pydantic validation schemas
│   │   └── services/      # Business logic (RAG, VectorSearch, ActionGraph, OCR)
│   ├── tests/             # Comprehensive unit, integration, and security test suites
│   └── Dockerfile         # Multi-stage production backend container
├── database/              # Alembic migration scripts (001 - 008)
├── frontend/
│   ├── src/
│   │   ├── components/    # UI widgets (AnalysisCard, ActionGraph, ReplyDraft, Viewer)
│   │   ├── context/       # AuthContext and non-blocking ToastContext
│   │   ├── pages/         # Views (InboxDashboard, Documents, SearchRAG, ActionGraph)
│   │   └── services/      # Type-safe API client layer
│   └── Dockerfile         # Nginx Alpine production static frontend
├── tests/                 # Automated 5-tier E2E test suites (76 tests)
├── docker-compose.yml     # Local orchestration (PostgreSQL + Backend + Frontend)
├── render.yaml            # Render infrastructure-as-code deployment specification
├── USER_GUIDE.md          # Comprehensive user manual and operating instructions
└── README.md              # Project documentation and engineering reference
```

---

## 📄 License

Developed as an enterprise work-intelligence engineering project. See [USER_GUIDE.md](USER_GUIDE.md) for full operational instructions.
