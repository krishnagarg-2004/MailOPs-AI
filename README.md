# MailOps AI (`EnterpriseAIMailOPs_MIPRO`)

MailOps AI is an AI-powered enterprise work-intelligence platform that connects organizational communication (emails) and business documents, understands content and relationships, extracts actionable work information, provides contextual knowledge retrieval, identifies tasks, decisions, deadlines, and risks, assists with human-reviewed responses, and presents explainable intelligence through a unified workspace.

---

## Project Structure

```
EnterpriseAIMailOPs_MIPRO/
│
├── EnterpriseAIMailOPs_MIPRO.txt         # Compatibility Project Bible Reference
├── PROJECT_BIBLE.md                     # Canonical Master Project Specification
├── PROJECT_STATUS.md                     # Milestone Progress & Status Tracker
├── README.md                             # Project Overview & Setup Guide
├── .gitignore                            # Root Git Exclusions
├── .env.example                          # Environment Template
├── requirements.txt                      # Derived Python Dependencies Manifest
│
├── backend/                              # FastAPI Backend Modular Monolith
│   ├── pyproject.toml                    # Authoritative Python Package Config
│   ├── README.md                         # Backend Documentation
│   ├── app/                              # Core Application Source Code
│   │   ├── main.py                       # FastAPI Entrypoint (Health check stub)
│   │   └── core/                         # Settings & Configuration
│   └── tests/                            # Test Suite (Pytest)
│
├── frontend/                             # React + TypeScript Web Workspace
│   ├── package.json                      # Node Package Manifest
│   ├── tsconfig.json                     # TypeScript Configuration
│   ├── vite.config.ts                    # Vite Configuration
│   └── src/                              # React Components & Feature Modules
│
├── database/                             # Migrations & Database Seeds
├── docs/                                 # Technical Architecture & Requirements Docs
├── scripts/                              # Automation Scripts
├── assets/                               # Static Media & Diagrams
├── docker/                               # Container Configurations
└── .github/                              # CI/CD Workflows
```

---

## Quick Start (Local Development)

### Prerequisites
- Python 3.14+
- Node.js v20+ / npm v10+

### Backend Setup
1. Create virtual environment:
   ```bash
   py -3.14 -m venv .venv
   ```
2. Activate virtual environment:
   - PowerShell: `.\.venv\Scripts\Activate.ps1`
   - Command Prompt: `.\.venv\Scripts\activate.bat`
3. Install backend dependencies:
   ```bash
   pip install -e ./backend
   ```
4. Start local PostgreSQL environment (Docker):
   ```bash
   docker compose up -d
   ```
5. Apply database migrations:
   ```bash
   alembic upgrade head
   ```
6. Run backend test suite:
   ```bash
   $env:PYTHONPATH="."
   .\.venv\Scripts\python -m pytest backend/tests
   ```
7. Launch FastAPI dev server:
   ```bash
   uvicorn backend.app.main:app --reload
   ```
   Access health check at `http://localhost:8000/api/v1/health`.


### Frontend Setup
1. Navigate to frontend directory:
   ```bash
   cd frontend
   ```
2. Install Node dependencies:
   ```bash
   npm install
   ```
3. Run Vite development server:
   ```bash
   npm run dev
   ```
4. Build frontend bundle:
   ```bash
   npm run build
   ```

---

## Documentation

- [PROJECT_BIBLE.md](file:///c:/Users/krish/Projects/EnterpriseAIMailOPs_MIPRO/PROJECT_BIBLE.md) — Comprehensive technical master specification.
- [PROJECT_STATUS.md](file:///c:/Users/krish/Projects/EnterpriseAIMailOPs_MIPRO/PROJECT_STATUS.md) — Current development status and roadmap milestones.
- `docs/` directory for architecture, API specs, security policies, and decision logs.
