# MailOps AI

> **Enterprise Work-Intelligence, Grounded RAG & Action Graph Platform**  
> Transform unstructured emails, attachments, contracts, and invoices into an explainable, relational operational knowledge layer.

[![Backend Tests](https://img.shields.io/badge/pytest-145%2F145%20passed%20(100%25)-success?style=flat-square)](backend/tests/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react)](https://react.dev/)
[![pgvector](https://img.shields.io/badge/pgvector-0.7+-336791?style=flat-square&logo=postgresql)](https://github.com/pgvector/pgvector)
[![Docker](https://img.shields.io/badge/Docker-Compose%20Ready-2496ED?style=flat-square&logo=docker)](docker-compose.yml)
[![Status](https://img.shields.io/badge/Status-Production--Ready-brightgreen?style=flat-square)](PROJECT_STATUS.md)

---

## 🌟 Overview

Modern enterprise communication is fragmented across emails, threads, invoices, and legal contracts. Critical action items, decisions, commitments, deadlines, and dependencies are easily overlooked.

**MailOps AI** bridges this gap by unifying communication ingestion with deep multi-layer AI intelligence:
- **Understands Content:** Performs semantic parsing, priority scoring, risk identification, and structured entity extraction.
- **Maps Relationships:** Models dependencies across email threads, tasks, documents, and stakeholders in an interactive **Action Graph** with BFS blocking-path traversal.
- **Retrieves Knowledge:** Provides 768-dimensional vector embeddings with cross-encoder re-ranking for **Grounded RAG** answers with source and page citations.
- **Empowers Action:** Assists with human-in-the-loop AI reply drafting and 1-click Google Calendar scheduling.

---

## 🚀 Quickstart with Docker (One Command)

Launch the full production stack (PostgreSQL 16 + pgvector, FastAPI backend, and Nginx React frontend) with a single command:

```bash
docker compose up -d
```

### Service Endpoints

| Service | URL | Description |
|---|---|---|
| **Frontend Application** | [http://localhost:3000](http://localhost:3000) | Desktop-class 3-pane client with dark theme |
| **Backend REST API** | [http://localhost:8000](http://localhost:8000) | FastAPI async REST endpoints |
| **Interactive API Docs** | [http://localhost:8000/docs](http://localhost:8000/docs) | OpenAPI / Swagger interactive documentation |
| **Health & Prometheus** | [http://localhost:8000/api/v1/webhooks/metrics](http://localhost:8000/api/v1/webhooks/metrics) | Real-time queue metrics, uptime, throughput |

> **⚡ Instant Demo Mode:** You do not need a live Google OAuth setup or Gemini API key to test the platform. Click **"⚡ Seed Demo"** on the login screen or dashboard to instantly load realistic enterprise escalation threads, multi-page invoices, and action graph dependencies.

---

## 🏗️ Architecture

```
                                  ┌───────────────────────────┐
                                  │   Desktop-Class 3-Pane    │
                                  │   React 18 + Vite UI      │
                                  └─────────────┬─────────────┘
                                                │ REST / OAuth Cookies
                                                ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ FastAPI Application Core (Modular Monolith)                                            │
│                                                                                        │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────┐  │
│  │ Google OAuth 2.0 │  │ Ingestion & Sync │  │ AI Intelligence  │  │ Action Graph   │  │
│  │ Multi-Tenant     │  │ Gmail REST &     │  │ Summaries, Tasks │  │ BFS Dependency │  │
│  │ Auth Sessions    │  │ Pub/Sub Webhooks │  │ Risks & Sentiments│ │ Resolution     │  │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘  └────────────────┘  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────┐  │
│  │ Document OCR     │  │ pgvector Search  │  │ Grounded RAG     │  │ Human-in-Loop  │  │
│  │ PDF/DOCX/Images  │  │ Semantic+Hybrid  │  │ Cross-Encoder    │  │ Reply Copilot  │  │
│  │ Tesseract Engine │  │ 768-d Cosine     │  │ Citation Synthesizer│ GCal Schedule │  │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘  └────────────────┘  │
└───────────────────────────────────────┬────────────────────────────────────────────────┘
                                        │ SQLAlchemy 2.0
                                        ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ PostgreSQL 16 + pgvector Database                                                      │
│                                                                                        │
│  • users & oauth_accounts        • email_threads & email_messages                      │
│  • document_extractions          • vector_embeddings (768-d ivfflat)                   │
│  • graph_nodes & graph_edges     • reply_drafts & audit_logs                           │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## ✨ Key Features

### 1. Ingestion & Communication
* **Gmail OAuth 2.0 Integration:** Scoped, user-isolated synchronization of threads, messages, and attachments.
* **Connection Pooling & Resiliency:** Pooled `httpx.AsyncClient` with exponential backoff for rate limits (`429`/`403`) and connection pacing.
* **Pub/Sub Real-Time Push:** Google Cloud Pub/Sub webhook endpoint (`POST /api/v1/webhooks/gmail`) for instant inbound processing.

### 2. AI Work Intelligence
* **Contextual Executive Summaries:** Multi-domain heuristic and Gemini models producing comprehensive summaries for CI/CD failures, invoices, contracts, and general operations.
* **Action & Risk Extraction:** Identifies granular tasks, assignees, deadlines, evidence snippets, and operational risks.
* **Explainability Drawer:** High-confidence scoring gauge with reasoning breakdown.

### 3. Document Intelligence & OCR
* **Multi-Format Extraction:** Native parser for PDF, DOCX, PNG, and JPEG.
* **OCR Fallback:** Automated Tesseract OCR fallback for scanned receipts, handwritten notes, and image attachments.
* **Business Extractions:** Structured invoice field parsing (vendor, total, tax/GST, due date) and contract terms.

### 4. Semantic Search & Grounded RAG
* **pgvector Search:** Fast 768-dimensional cosine similarity (`<=>`) and hybrid search combining keyword and vector scoring via Reciprocal Rank Fusion (RRF).
* **Dual Method Endpoints:** Supports both `GET ?q=...` and `POST` JSON payloads on search routes.
* **Grounded Answer Synthesis:** Answers questions strictly based on retrieved context with explicit file and page citations (`[Source: Invoice.pdf, Page 1]`).
* **1-Click Mailbox Re-Indexing:** UI trigger to batch chunk and embed mailboxes into pgvector.

### 5. Action Graph & BFS Dependency Engine
* **Relational Graph:** Models nodes (`EMAIL_THREAD`, `ACTION_ITEM`, `INVOICE`, `CONTRACT`, `DECISION`, `RISK`, `PERSON`) and edges (`BLOCKS`, `DEPENDS_ON`, `ASSIGNED_TO`).
* **BFS Traversal:** Walks multi-hop dependency chains to detect blockers holding up critical tasks.
* **Interactive Canvas & Grid:** Toggle between visual drag-and-pan canvas and structured cards.

### 6. Human-in-the-Loop Reply Copilot
* **Contextual Draft Generation:** Tone-adaptive AI drafts (`PROFESSIONAL`, `CONCISE`, `URGENT`).
* **Rich-Text Editor:** Formatting toolbar with inline Tab-to-accept ghost text autocomplete.
* **Controlled Dispatch:** Direct sync to Gmail drafts or explicit user-confirmed dispatch.
* **Google Calendar Scheduling:** 1-click scheduling for extracted deadlines and meetings.

---

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| **Backend** | Python 3.12 / 3.14, FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2 |
| **Frontend** | React 18, TypeScript 5.5, Vite, Tailwind CSS, Lucide Icons |
| **Database** | PostgreSQL 16 with `pgvector` (vector similarity search) |
| **AI / Embeddings** | Google Gemini (`google-genai`), `text-embedding-004`, Mock Fallback |
| **Document Processing** | PyPDF, python-docx, Pillow, pytesseract, pdf2image |
| **Containerization** | Docker, Docker Compose, Nginx Alpine |
| **Testing** | Pytest, pytest-asyncio, HTTPX TestClient |

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

# Frontend
VITE_API_BASE_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000
```

---

## 🧪 Testing & Verification

The test suite covers API endpoints, integration flows, document parsers, security isolation, multitenant audits, and prompt injection defense:

```bash
# Run complete test suite in Docker
docker exec mailops_backend pytest backend/tests/

# Or run locally in virtual environment
pytest backend/tests/
```

### Test Suite Results: **145 / 145 Tests Passing (100%)**

- **API Tests (20 tests):** Auth, Gmail sync, AI extraction, Document OCR, Action Graph, Reply Drafts, Search & RAG.
- **Integration Tests (33 tests):** Database migrations, OAuth lifecycle, Vector search, Reranker, Background queue, Calendar sync.
- **Security & Multi-Tenant Tests (18 tests):** User data isolation, Graph boundary checks, Secret leak audit, Prompt injection defense.
- **Evaluation Tests (3 tests):** AI extraction quality, Document parsing accuracy, RAG synthesis evaluation.
- **Unit Tests (71 tests):** Evidence validation, MIME parser, Chunking algorithms, Crypto token encryption.

---

## ☁️ Cloud Deployment (100% Free Tier)

Deploy MailOps AI online for free using this architecture:

```
[ Frontend: React / Vite ] ──> Render Static Site (Free, global CDN, custom domain)
            │
            ▼
[ Backend: FastAPI / Docker ] ──> Render Web Service (Free tier, auto-deploy from GitHub)
            │                         ▲
            │                         │ (Free 5-min ping keeps backend awake)
            ▼                   [ UptimeRobot ]
[ Database: PostgreSQL + pgvector ] ──> Supabase (Free tier, persistent 500 MB)
```

1. **Database (Supabase):** Create a free project at [supabase.com](https://supabase.com). In Database → Extensions, enable `vector`. Copy your PostgreSQL connection URI.
2. **Backend (Render):** Create a new **Web Service** pointing to your GitHub repo. Select `Docker` environment and supply `DATABASE_URL` from Supabase.
3. **Frontend (Render):** Create a **Static Site** pointing to `/frontend`. Build command: `npm install && npm run build`, publish directory: `dist`. Set `VITE_API_BASE_URL` to your Render backend URL.
4. **Uptime Monitoring:** Create a free HTTP monitor at [uptimerobot.com](https://uptimerobot.com) pinging `https://<your-backend>.onrender.com/api/v1/health` every 5 minutes to prevent idle sleep.

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
│   ├── tests/             # 145 unit, integration, api, and security tests
│   └── Dockerfile         # Multi-stage production backend container
├── database/              # Alembic migration scripts (001 - 008)
├── frontend/
│   ├── src/
│   │   ├── components/    # Reusable UI widgets (Analysis, Graph, Reply, Viewer)
│   │   ├── pages/         # Views (InboxDashboard, Documents, SearchRAG, ActionGraph)
│   │   └── services/      # Type-safe API client layer
│   └── Dockerfile         # Nginx Alpine production static frontend
├── docker-compose.yml     # Local orchestration (PostgreSQL + Backend + Frontend)
├── PROJECT_STATUS.md      # Detailed milestone audit & engineering logs
└── README.md              # Project documentation and quickstart
```

---

## 📄 License

Developed as an enterprise work-intelligence engineering project. See [PROJECT_STATUS.md](PROJECT_STATUS.md) for detailed milestone progress and changelogs.
