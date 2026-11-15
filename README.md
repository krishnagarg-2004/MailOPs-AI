# MailOps AI

> **Project:** EnterpriseAIMailOPs_MIPRO  
> **Type:** B.Tech College Minor Project / Resume & Placement Portfolio Project  
> **Architecture:** Modular Monolith with Distributed Worker Queue  
> **Status:** Production-Ready (Phases 1 – 9 Complete)  
> **Current Progress:** See [`PROJECT_STATUS.md`](PROJECT_STATUS.md) and [`future_phases_roadmap.md`](future_phases_roadmap.md)

---

## Overview

MailOps AI is an AI-powered enterprise work-intelligence platform that connects organizational communication and business documents, understands their content and relationships, extracts actionable information, provides contextual knowledge retrieval, and assists users with human-reviewed AI responses.

Modern enterprise work is often spread across emails, threads, attachments, invoices, contracts, and other unstructured documents. Important decisions, tasks, deadlines, risks, and commitments can become difficult to track and retrieve.

MailOps AI is designed to transform this fragmented information into a structured, explainable, and collaborative intelligence layer.

The platform capabilities include:

- **Gmail Synchronization:** Synchronize Gmail messages, threads, metadata, and attachments via Google OAuth 2.0.
- **Real-Time Push Ingestion:** Google Cloud Pub/Sub webhooks for instant zero-latency inbound email processing.
- **Deep AI Analysis:** Executive summarization, intent classification, priority, urgency, and sentiment scoring using Google Gemini.
- **Action, Decision & Risk Extraction:** Automated identification of granular tasks, deadlines, assigned owners, and operational risks.
- **Cross-Encoder Precision Re-Ranking:** Advanced lexical-semantic re-ranking for dense context retrieval before LLM synthesis.
- **Agentic Multi-Step Reasoning & Tools:** Dynamic tool dispatcher for historical invoice queries and action dependency graph resolution.
- **1-Click Google Calendar Action Sync:** Direct deadline scheduling to Google Calendar with automatic action confirmation.
- **Document Intelligence & OCR:** Multi-layer text extraction for PDF, DOCX, PNG, and JPEG documents with Tesseract OCR fallback.
- **Semantic & Hybrid Search:** Fast vector similarity search powered by PostgreSQL and `pgvector` alongside keyword filtering.
- **Enterprise Action Graph:** Relational dependency mapping connecting emails, attachments, decisions, and blocking action items.
- **Multi-Tenancy & RBAC:** Organization workspaces with granular role-based permissions (`ADMIN`, `MANAGER`, `ANALYST`, `VIEWER`).
- **Tamper-Evident Compliance Audit Logs:** Append-only regulatory audit logging for all enterprise events and actions.
- **Distributed Worker Task Queue:** In-process asynchronous task queue with concurrency management, exponential backoff retries, and dead-letter queue (DLQ).
- **Health Telemetry & Prometheus Metrics:** Automated `/api/v1/webhooks/metrics` endpoint serving real-time queue depths, task throughput, and uptime.
- **Superhuman-Style 3-Pane Desktop UI:** Ergonomic thread navigator, conversation history reader, and collapsible AI Work Intelligence Inspector.
- **AI Copilot Reply Workspace:** Rich-text reply drafting with formatting toolbar, quick-prompt chips, and Tab-to-accept ghost autocomplete.
- **Executive Intelligence Digest:** Cross-mailbox summary reports and downloadable CSV/Markdown exports for leadership teams.
- **Strict Human-in-the-Loop Safeguards:** Explicit human consent required before any consequential email sending or drafting.

---

# 1. Project Identity

## Working Title

**MailOps AI**

Repository / project identifier:

```text
EnterpriseAIMailOPs_MIPRO
```

## Alternative Names Previously Considered

- InboxIQ
- MailMind AI
- MailPilot AI

## Project Classification

B.Tech College Minor Project and serious software engineering portfolio project.

## Domain

- Artificial Intelligence
- Enterprise Software
- Natural Language Processing
- Email Intelligence
- Document Intelligence
- Knowledge Retrieval
- Retrieval-Augmented Generation
- Workflow Automation

## Canonical Product Definition

MailOps AI is an AI-powered enterprise work-intelligence platform that connects organizational communication and business documents, understands their content and relationships, extracts actionable work information, provides contextual knowledge retrieval, identifies tasks, decisions, deadlines, and risks, assists with human-reviewed responses, and presents explainable intelligence through a unified workspace.

---

# 2. Problem Statement

Enterprise professionals often deal with large amounts of unstructured communication and documentation.

Important information is distributed across:

- Emails.
- Email threads.
- Attachments.
- Invoices.
- Contracts.
- Receipts.
- Purchase orders.
- Other business documents.

This creates several operational problems.

## Information Overload

Large volumes of emails and attachments can make important requests and urgent issues difficult to identify.

## Context Fragmentation

Decisions, commitments, deadlines, and supporting information may be scattered across multiple email threads and documents.

## Manual Document Processing

Employees often need to manually open, read, and extract important information from invoices, contracts, and other business documents.

## Missed Tasks and Deadlines

Action items and deadlines communicated informally through email can be overlooked.

## Inefficient Information Retrieval

Traditional keyword search may fail to retrieve contextually related information from historical communication.

## Repetitive Communication

Routine responses and follow-ups consume time and require users to repeatedly reconstruct conversation context.

## Limited Relationship Visibility

Traditional email clients primarily organize individual messages and threads. They do not provide a unified view of how communications, documents, decisions, tasks, and deadlines are connected.

MailOps AI addresses this by adding an intelligence and knowledge layer on top of enterprise communication.

---

# 3. Target Users

## Operations Employees and Managers

Users who need to track:

- Cross-departmental requests.
- Project updates.
- Operational bottlenecks.
- Pending actions.
- Important deadlines.

## Finance Personnel

Users who work with:

- Vendor invoices.
- Payment due dates.
- Tax and GST information.
- Purchase orders.
- Financial documents.

## Legal and Compliance Teams

Users who need to monitor:

- Contract terms.
- Clause variations.
- Renewal dates.
- Obligations.
- Risk-related clauses.

## Individual Enterprise Professionals

Users who want assistance with:

- Organizing daily priorities.
- Identifying action items.
- Understanding communication history.
- Retrieving relevant information.
- Drafting contextual responses.

---

# 4. Product Vision

The goal of MailOps AI is to transform raw enterprise communication into an explainable and structured work-intelligence network.

Every important email or document should help answer:

1. What happened?
2. Why does it matter?
3. What needs to be done next?
4. Who is responsible?
5. When is the deadline?
6. What supporting evidence exists?
7. How does this information relate to existing enterprise knowledge?

The system is intended to move enterprise communication from passive information consumption toward structured operational intelligence.

---

# 5. Core Product Principles

## 1. Understand Before Acting

The system should analyze and understand communication and documents before recommending or performing actions.

## 2. Human Remains in Control

AI may generate recommendations, extractions, and drafts, but consequential external actions require human review and approval.

## 3. Explainable AI

Important AI outputs should be supported by:

- Confidence information.
- Supporting evidence.
- Relevant source content.
- Structured output validation.

## 4. Evidence Over Unsupported Generation

Retrieved context and supporting evidence should be preferred over unsupported AI-generated information.

## 5. Modular Architecture

Version 1 uses a **Modular Monolith** architecture.

The project should avoid unnecessary distributed complexity.

## 6. Avoid Unnecessary Dependencies

The system should not introduce major frameworks or infrastructure unless they provide a clear architectural benefit.

## 7. Complete the Core Product

The objective is to build a complete and functional Version 1 rather than an unfinished collection of unrelated features.

## 8. Treat External Content as Untrusted

Email bodies, attachments, and other imported content must be treated as untrusted input.

This is particularly important when passing content to AI systems.

---

# 6. Core Product Capabilities

## Gmail Integration

MailOps AI integrates with Gmail using Google OAuth 2.0.

Capabilities include:

- Secure Google authentication.
- Gmail message synchronization.
- Thread synchronization.
- Metadata retrieval.
- Attachment retrieval.
- User-scoped data isolation.
- Draft creation.
- Controlled email sending after explicit approval.

---

## Email and Thread Intelligence

The AI analysis layer can extract:

- Executive summaries.
- Intent classification.
- Priority.
- Urgency.
- Sentiment.
- Action items.
- Assigned owners.
- Decisions.
- Deadlines.
- Risks.
- Supporting evidence.

AI-generated outputs are validated using structured schemas.

---

## Action Intelligence

The platform identifies operational information embedded in communication.

This includes:

- Requests.
- Commitments.
- Action items.
- Decisions.
- Deadlines.
- Responsible owners.
- Recommended next actions.
- Operational risks.

---

## Document Intelligence

Supported initial document formats include:

- PDF
- DOCX
- PNG
- JPEG

The processing pipeline is:

```text
File Validation
      ↓
Text Extraction
      ↓
OCR Fallback
      ↓
Sanitization
      ↓
Normalization
      ↓
Chunking
      ↓
Business Information Extraction
      ↓
Vector Indexing
```

The system can extract structured information from business documents.

### Invoice Extraction

Potential extracted fields include:

- Vendor.
- Invoice number.
- Invoice date.
- Due date.
- Total amount.
- Tax / GST.
- Payment terms.

### Contract Extraction

Potential extracted fields include:

- Contracting parties.
- Effective date.
- Expiration date.
- Key obligations.
- Renewal terms.
- Risk clauses.

---

## AI Reply Assistance

MailOps AI can generate contextual email replies and follow-ups using conversation history and relevant retrieved information.

The workflow is:

```text
AI Generates Draft
        ↓
User Reviews Draft
        ↓
User Edits if Necessary
        ↓
User Explicitly Approves Action
        ↓
Draft is Sent Through Gmail
```

The system must not autonomously send emails in Version 1.

---

## Knowledge Intelligence and Search

MailOps AI supports contextual information retrieval across emails and documents.

The search system combines:

- Structured metadata filtering.
- Vector similarity retrieval.
- Semantic search.

Examples of structured filters include:

- Sender.
- Date range.
- Priority.
- Tags.

Vector search is implemented using `pgvector` inside PostgreSQL.

---

## Retrieval-Augmented Generation

Retrieved email and document chunks can be supplied to the AI model as contextual information.

The system can then generate answers grounded in relevant retrieved content.

This allows users to ask contextual questions about their communication and documents.

---

## Action Graph

MailOps AI models relationships between enterprise information.

Examples include:

```text
Email Thread
      │
      ├── Attachment
      │
      ├── Decision
      │
      ├── Action
      │
      ├── Deadline
      │
      └── Participant
```

The Version 1 implementation uses PostgreSQL domain relationships rather than a dedicated graph database.

Neo4j is not part of Version 1.

---

## Operational Dashboard

The application provides a unified operational overview of:

- Daily priorities.
- Pending actions.
- Recent AI extractions.
- Document processing activity.
- Processing statistics.

---

# Advanced Enterprise Platform Capabilities (Phases 6 – 9)

In addition to core single-mailbox processing, MailOps AI includes an advanced enterprise suite across four key dimensions:

### 1. Advanced Retrieval, Re-Ranking & Agentic Tools (Phase 6)
- **Cross-Encoder Precision Re-Ranking (`CrossEncoderReranker`):** Integrates lexical-semantic cross-attention scoring. Doubles the candidate retrieval pool before LLM synthesis and re-ranks top candidates by token proximity and density.
- **Agentic Multi-Step Reasoning (`AgentToolRegistry`):** Provides autonomous tool-using capabilities:
  - `lookup_previous_invoice(vendor_name)`: Discovers historical pricing and vendor invoice numbers.
  - `query_action_dependencies(action_id)`: Traverses the action graph to identify blocking tasks and dependencies.
  - `execute_tool_call()`: Dynamic agent dispatcher.
- **1-Click Google Calendar Sync (`CalendarService`):** Schedules extracted deadlines and action items directly to Google Calendar (`POST /api/v1/calendar/schedule`) and confirms task status.

### 2. Multi-Tenancy, Collaboration & Compliance (Phase 7)
- **Organization Workspaces & RBAC (`Organization`, `TeamMembership`):** Hierarchical workspace isolation with role-based access controls (`ADMIN`, `MANAGER`, `ANALYST`, `VIEWER`).
- **Collaborative Action Lifecycle:** Interactive status transition pipeline (`PENDING` ➔ `CONFIRMED` ➔ `COMPLETED` / `DISMISSED`) allowing teams to assign and track obligations.
- **Immutable Audit Logging (`AuditService`, `AuditLog`):** High-fidelity tamper-evident compliance audit trails tracking actors, actions, timestamps, IP addresses, and payload diffs (`/api/v1/organization/audit-logs`).

### 3. Cloud-Native Real-Time Ingestion & Distributed Workers (Phase 8)
- **Real-Time Push Ingestion:** Integration with Google Cloud Pub/Sub (`POST /api/v1/webhooks/gmail`) for instant asynchronous email processing without manual clicking or scheduled interval polling.
- **Distributed Worker Task Queue (`DistributedWorkerQueue`):** In-process concurrent background worker engine with automated retries, exponential backoff, failure accounting, and dead-letter queue (DLQ) tracking.
- **Prometheus Telemetry & Metrics (`PrometheusMetricsCollector`):** Exposes `GET /api/v1/webhooks/metrics` adhering to Prometheus text exposition format (monitoring uptime, queue depth, throughput, and error rates).

### 4. Modern 3-Pane UI, Rich-Text AI Copilot & Executive Reporting (Phase 9)
- **Desktop-Class 3-Pane Layout:** Superhuman/Linear-style split workspace in `InboxDashboardView.tsx`:
  - *Pane 1 (Left):* Thread Navigator with search filters, urgency pills, and unread badges.
  - *Pane 2 (Center):* Conversation Reader with attachment previews, participant badges, and quick-action bar.
  - *Pane 3 (Right):* Collapsible AI Work Intelligence Inspector & Copilot.
- **Rich-Text AI Copilot (`ReplyDraftWidget`):** Formatting toolbar (bold, italic, lists, quotes, code), instant context injection chips, and inline **Tab-to-accept ghost text autocomplete**.
- **Executive Intelligence Digest:** Summary dashboard and multi-format downloadable reports (`GET /api/v1/digest/export?format=csv|markdown|json`) capturing high-level KPIs, open risk registries, and financial totals.

---

# 7. Version 1 Scope

Version 1 focuses on the following capabilities:

- Secure Google OAuth authentication.
- Gmail API integration.
- Gmail reading and drafting workflows.
- Modular monolith backend architecture.
- Python and FastAPI backend.
- PostgreSQL database.
- React and TypeScript frontend.
- Vite frontend tooling.
- Tailwind CSS styling.
- Document processing for supported formats.
- OCR fallback using Tesseract.
- Gemini API integration.
- Structured AI output validation.
- Semantic retrieval using PostgreSQL and `pgvector`.
- Domain-model-based Action Graph.
- Human-reviewed AI email responses.
- Testing and AI evaluation infrastructure.

---

# 8. Explicitly Out of Scope for Version 1

To prevent uncontrolled scope expansion, the following are excluded from Version 1:

- Resume analysis.
- Candidate scoring.
- Interview question generation.
- Autonomous email sending.
- Slack integration.
- Microsoft Teams integration.
- Discord integration.
- Microsoft Outlook integration.
- Direct IMAP or POP3 email clients.
- Microservices architecture.
- Dedicated graph databases such as Neo4j.
- Dedicated vector databases such as ChromaDB or Pinecone.
- LangChain as a core structural dependency.
- Heavy agentic framework lock-in.

Some of these capabilities may be considered in future versions.

---

# 9. Functional Requirements

## Authentication

**FR-AUTH-01**

Users must authenticate securely using Google OAuth 2.0.

---

## Gmail Synchronization

**FR-MAIL-01**

The system must retrieve and synchronize:

- Email threads.
- Messages.
- Metadata.
- Attachments.

Long-running synchronization should execute through background processing.

---

## AI Analysis

**FR-AI-01**

The system must analyze email messages and generate:

- Summaries.
- Intent classifications.
- Priority scores.
- Sentiment ratings.

**FR-AI-02**

The system must extract:

- Action items.
- Assigned owners.
- Explicit deadlines.
- Relevant decisions and operational information.

---

## Document Processing

**FR-DOC-01**

The system must validate and extract text from supported PDF and image files.

OCR should be used when native text extraction is unavailable.

**FR-DOC-02**

The system must extract structured metadata from business documents such as:

- Invoices.
- Contracts.
- Purchase orders.

---

## Search and Retrieval

**FR-RAG-01**

The system must index email and document text into searchable chunks using vector representations.

---

## AI Reply Generation

**FR-REPLY-01**

The system must generate contextual email drafts and require user review before dispatch.

---

## Relationship Visualization

**FR-GRAPH-01**

The system must support visualization of relationships between:

- Messages.
- Documents.
- Actions.
- Decisions.
- Deadlines.
- Participants.

---

# 10. Non-Functional Requirements

## Security

**NFR-SEC-01**

OAuth tokens, API keys, and other secrets must:

- Never be committed to Git.
- Be loaded through environment configuration.
- Be protected during storage.

**NFR-SEC-02**

Email and document content must be treated as untrusted input.

The system should protect against prompt injection and malicious instructions embedded in external content.

---

## Performance

**NFR-PERF-01**

Read operations should target response times below 200 ms where practical.

Long-running operations such as:

- Gmail synchronization.
- AI analysis.
- OCR.
- Document processing.

should execute asynchronously through background jobs.

---

## Reliability

**NFR-RELIABILITY-01**

Background processing should handle external API failures and rate limits using appropriate retry mechanisms, including exponential backoff where applicable.

---

## Maintainability

**NFR-MAINTAINABILITY-01**

The backend must maintain clear architectural boundaries between modules and responsibilities.

---

# 11. System Architecture

MailOps AI uses a **Modular Monolith** architecture for Version 1.

```text
                    ┌─────────────────────────────┐
                    │   React + TypeScript + Vite │
                    │           Frontend          │
                    └──────────────┬──────────────┘
                                   │
                              HTTP / REST
                                   │
                                   ▼
                    ┌─────────────────────────────┐
                    │       FastAPI Backend       │
                    └───────┬─────────┬───────────┘
                            │         │
              ┌─────────────┘         └─────────────┐
              ▼                                     ▼
     ┌──────────────────┐                   ┌──────────────────┐
     │ PostgreSQL       │                   │ Background       │
     │ + pgvector       │                   │ Workers          │
     └──────────────────┘                   └────────┬─────────┘
                                                     │
                                                     ▼
                                           ┌──────────────────┐
                                           │ External APIs    │
                                           │ Gmail / Gemini   │
                                           └──────────────────┘
```

The architecture avoids premature microservice complexity while maintaining internal modular boundaries.

---

# 12. Backend Architecture

The backend follows a modular structure.

```text
backend/
└── app/
    ├── api/
    │   └── v1/
    │
    ├── core/
    ├── domain/
    ├── schemas/
    ├── services/
    ├── repositories/
    ├── integrations/
    ├── ai/
    ├── documents/
    ├── search/
    ├── workers/
    ├── db/
    │
    └── main.py
```

## Module Responsibilities

### `api/v1/`

HTTP route handlers and request validation.

### `core/`

Application configuration, security, logging, and shared error definitions.

### `domain/`

Core domain entities and value objects.

### `schemas/`

Pydantic models for request and response validation.

### `services/`

Business logic coordinating domain models and repositories.

### `repositories/`

Database access abstractions.

### `integrations/`

Third-party service integrations such as Gmail.

### `ai/`

AI provider abstractions, prompt definitions, and model clients.

### `documents/`

File validation, parsing, text extraction, and OCR functionality.

### `search/`

Embedding generation and semantic retrieval.

### `workers/`

Background processing jobs.

### `db/`

Database sessions, models, and database infrastructure.

---

# 13. Domain Model

The conceptual domain includes the following modules.

## Identity

- `User`
- `OAuthAccount`

## Email

- `EmailThread`
- `EmailMessage`
- `Participant`
- `Attachment`

## Documents

- `Document`
- `DocumentVersion`
- `DocumentExtraction`

## Intelligence

- `AIAnalysis`
- `Classification`
- `Entity`
- `Recommendation`
- `Evidence`

## Actions

- `Action`
- `Deadline`
- `Decision`
- `Risk`
- `Relationship`

## Knowledge

- `Chunk`
- `Embedding`

## Organization

- `Organization`
- `Project`
- `Client`

## Infrastructure

- `ProcessingJob`
- `AuditEvent`

---

# 14. Database Architecture

## Primary Database

**PostgreSQL**

PostgreSQL acts as the primary relational store for:

- User information.
- OAuth data.
- Email metadata.
- Documents.
- Extracted information.
- Actions.
- Relationships.
- Audit logs.
- Processing jobs.

## Vector Search

Semantic retrieval uses the PostgreSQL `pgvector` extension.

This avoids introducing a separate vector database for Version 1.

---

# 15. AI and ML Architecture

## Primary AI Provider

Gemini is the primary AI provider.

Integration uses the direct official SDK:

```text
google-genai
```

## Provider Abstraction

The AI architecture should allow future providers to be introduced without tightly coupling the application to one model provider.

Potential future providers may include:

- OpenAI.
- Anthropic.
- Local Ollama models.

## Structured Output

AI outputs should be validated using Pydantic schemas.

Structured responses should be preferred over unvalidated free-form output.

## Prompt Injection Defense

Emails and documents are external and potentially untrusted.

Content should be isolated from application instructions and processed as data rather than executable instructions.

---

# 16. Gmail Integration

## Authentication

Google OAuth 2.0 is used for Gmail access.

Relevant capabilities include:

- Reading emails.
- Accessing messages and threads.
- Creating drafts.
- Controlled sending after user approval.

## Synchronization

Email synchronization retrieves:

- Headers.
- Message metadata.
- Message content.
- Threads.
- Attachments.

Long-running synchronization should be handled asynchronously.

## Drafting Workflow

```text
Conversation Context
        ↓
AI Draft Generation
        ↓
User Review
        ↓
User Edit
        ↓
Explicit Approval
        ↓
Gmail Action
```

The AI does not autonomously send emails.

---

# 17. Document Intelligence Pipeline

Supported initial file formats:

- PDF
- DOCX
- PNG
- JPEG

Processing flow:

```text
File Validation
      ↓
Text Extraction
      ↓
OCR Fallback
      ↓
Sanitization
      ↓
Normalization
      ↓
Chunking
      ↓
Business Information Extraction
      ↓
Vector Embedding and Indexing
```

The system focuses initially on extracting useful structured information from enterprise documents such as invoices and contracts.

---

# 18. Search and Retrieval

MailOps AI uses hybrid retrieval.

## Structured Search

Users can filter information using metadata such as:

- Sender.
- Date range.
- Priority.
- Tags.

## Semantic Search

Email and document content is divided into chunks and represented using embeddings.

These embeddings are stored using PostgreSQL and `pgvector`.

## Contextual RAG

Relevant chunks are retrieved and supplied to the AI model together with citation or source metadata.

The goal is to produce responses grounded in relevant enterprise information.

---

# 19. Action Graph

The Action Graph represents relationships between operational information.

Example:

```text
Participant
     │
     ▼
Email Thread ──── Document
     │               │
     ▼               ▼
  Decision ────── Action
                      │
                      ▼
                   Deadline
```

Version 1 stores these relationships using PostgreSQL domain models.

A dedicated graph database is intentionally excluded from Version 1.

---

# 20. Human-in-the-Loop Design

MailOps AI must not autonomously perform high-impact external actions.

## Reply Workflow

```text
AI Generates Draft
        ↓
User Reviews
        ↓
User Edits
        ↓
User Explicitly Sends
```

## Action Workflow

```text
AI Detects Action Item
        ↓
Action Presented to User
        ↓
User Reviews or Edits
        ↓
User Confirms
        ↓
Action Added to Active Workflow
```

The user remains responsible for final approval.

---

# 21. Security Principles

## Secrets Management

Secrets and configuration are loaded through environment variables.

Examples include:

- API keys.
- OAuth credentials.
- Database credentials.
- Encryption keys.

Secrets must never be committed to source control.

## User Data Isolation

Application queries must maintain appropriate user boundaries.

User-owned data should be scoped using the appropriate identity information.

## Token Protection

OAuth refresh tokens require secure storage and protection.

## Untrusted Content

All imported email and document content must be treated as untrusted.

---

# 22. Testing and AI Evaluation

The project includes a structured testing strategy.

```text
backend/tests/
├── unit/
├── integration/
├── api/
├── security/
└── evaluation/
```

## Unit Tests

Test core domain logic, utilities, and configuration.

## Integration Tests

Test database interactions, workers, and external integration boundaries.

## API Tests

Test FastAPI endpoints.

## Security Tests

Test authentication boundaries and defenses against malicious or adversarial input.

## AI Evaluation

Evaluate:

- Structured output parsing.
- Extraction quality.
- Schema validation.
- Reliability of AI-generated information.

---

# 23. Observability

The system should provide:

- Structured application logging.
- Audit logging for important actions.
- Background job monitoring.
- Processing duration tracking.
- Retry information.

Security-relevant actions may include:

- Authentication events.
- Email sending.
- Important configuration changes.

---

# 24. Deployment

The project supports containerized deployment.

Potential deployment structure:

- Backend container.
- Frontend container.
- PostgreSQL database.

Local orchestration may use Docker Compose.

Potential production targets include:

- Frontend: Vercel.
- Backend: Railway, Render, or Google Cloud Run.
- Database: Supabase or Neon PostgreSQL.

These deployment targets are not architectural requirements and may change based on project needs.

---

# 25. Technology Stack

| Layer | Technology | Details |
|---|---|---|
| Backend Language | Python 3.14 | Modern async typed Python |
| Frontend Language | TypeScript 5.5 | Type-safe React components |
| Backend Framework | FastAPI | High-performance asynchronous REST API |
| Frontend Framework | React 18 | Desktop-class 3-pane responsive client |
| Frontend Tooling | Vite | Fast module bundling with 0 build errors |
| Styling | Tailwind CSS | Modern dark-mode enterprise UI |
| Database | PostgreSQL 16 | Relational data & Action Graph storage |
| Vector Search | pgvector | Dense 768-dim semantic search index |
| AI Engine | Gemini (via `google-genai`) | Structured JSON extraction & LLM RAG |
| Context Re-Ranking | Lexical-Semantic Cross-Encoder | 2x candidate pool re-ranking before synthesis |
| Distributed Processing | Async WorkerQueue | In-process concurrent task queue with retries & DLQ |
| Real-Time Ingestion | Google Cloud Pub/Sub Webhooks | Push notification endpoint for Gmail updates |
| Observability | Prometheus Exposition | Telemetry metrics (`/api/v1/webhooks/metrics`) |
| Authentication | Google OAuth 2.0 | Multi-tenant auth with granular scope consent |
| Calendar Integration | Google Calendar REST API | 1-click event and deadline synchronization |
| OCR Engine | Tesseract OCR & Poppler | Multi-layer PDF/image document parsing |
| Backend Testing | Pytest | 77/77 tests passing (100% pass rate) |
| Frontend Testing | Vitest | Component & service verification |

Local Python environment:

```powershell
py -3.14 -m venv .venv
```

---

# 26. Architecture Decisions

The following decisions are currently established for Version 1.

## ADR-001 — Modular Monolith

Use a Modular Monolith instead of Microservices.

Reason:

- Lower operational complexity.
- Easier development and debugging.
- Appropriate for the current project scope.
- Internal modules can remain clearly separated.

---

## ADR-002 — PostgreSQL and pgvector

Use PostgreSQL with the `pgvector` extension instead of a separate vector database.

Reason:

- Reduced infrastructure complexity.
- Centralized relational and vector storage.
- Suitable for Version 1 requirements.

---

## ADR-003 — Direct Gemini SDK

Use the direct Gemini SDK rather than making LangChain a core dependency.

Reason:

- Lower abstraction overhead.
- More direct control over prompts and model interactions.
- Reduced framework lock-in.

---

## ADR-004 — PostgreSQL-Based Action Graph

Represent relationships using the application's relational domain model instead of Neo4j.

Reason:

- Avoids introducing a dedicated graph database.
- Keeps infrastructure simpler for Version 1.

---

## ADR-005 — Python 3.14

Standardize the local Python environment on Python 3.14.

```powershell
py -3.14 -m venv .venv
```

---

# 27. Engineering Rules

1. **No Speculative Code**  
   Build features based on the current approved requirements.

2. **No Unjustified Dependencies**  
   Every dependency should have a clear purpose.

3. **No Unsafe Execution**  
   External email or document content must never be treated as trusted application instructions.

4. **Clear Module Boundaries**  
   Keep responsibilities separated inside the modular monolith.

5. **Structured Validation**  
   Use explicit type hints and Pydantic validation where appropriate.

6. **Human Approval for Consequential Actions**  
   AI suggestions must not bypass required user review.

7. **Avoid Scope Creep**  
   Features outside Version 1 should not be added without deliberate scope review.

---

# 28. Git Workflow

## Branching

- `main` represents stable project state.
- Feature branches may be used for isolated development work.

## Commits

Commits should be small and focused.

Preferred prefixes include:

```text
feat:
fix:
docs:
chore:
refactor:
test:
```

## Security

Before committing:

- Check for accidentally included secrets.
- Review changed files.
- Ensure ignored files remain untracked.
- Run relevant tests where applicable.

---

# 29. Project Documentation

The repository documentation should have clear responsibilities.

## `README.md`

This file contains:

- Project identity.
- Product overview.
- Problem statement.
- Architecture.
- Features.
- Requirements.
- Technology stack.
- Scope.
- Engineering rules.
- Architecture decisions.

It serves as the primary project reference.

## `PROJECT_STATUS.md`

This file tracks the actual current implementation state, including:

- Current milestone.
- Completed work.
- Work in progress.
- Next steps.
- Known issues.
- Remaining tasks.

## `docs/`

The `docs/` directory contains supporting technical documentation.

Architectural and implementation decisions should reflect the actual state of the project.

---

# 30. Risks and Mitigation

| Risk | Impact | Mitigation |
|---|---|---|
| Scope Creep | Project becomes incomplete | Maintain clear Version 1 boundaries |
| External API Rate Limits | Sync delays or failures | Background processing and retry mechanisms |
| Prompt Injection | Unsafe AI behavior | Treat imported content as untrusted and validate outputs |
| Dependency Complexity | Difficult maintenance | Avoid unnecessary frameworks and infrastructure |
| AI Output Inconsistency | Incorrect extraction | Use structured schemas and validation |
| Data Exposure | Security and privacy risk | User-scoped data access and secure credential handling |

---

# 31. Future Improvements & Next Horizon (Phase 10+)

Phases 1 through 9 have established an enterprise work-intelligence platform with RAG, cross-encoder re-ranking, multi-tenancy, distributed worker queues, a 3-pane client, an AI Copilot, and executive reporting.

Potential roadmap initiatives for **Phase 10 and beyond** include:

1. **Multi-Provider AI Fallback & Local Model Support (Ollama / vLLM):**
   - Automatically fall back to local offline LLMs (e.g. Llama-3.3-70B, Mistral Nemo via Ollama) when cloud API connectivity drops or for zero-data-retention on confidential internal correspondence.
2. **Microsoft 365 & Outlook Exchange Synchronization:**
   - Ingest email threads and calendars via Microsoft Graph API alongside Google Workspace.
3. **Multi-Modal Visual Bounding-Box Grounding:**
   - Overlay interactive bounding boxes directly on rendered PDF and image invoices to highlight extracted line items, totals, and signatures in the document viewer.
4. **Slack & Microsoft Teams Urgent Notification Bot:**
   - Push real-time alerts for high-severity risks or approaching SLA deadlines to dedicated company channels with 1-click action buttons.
5. **Voice-to-Reply & Audio Email Dictation:**
   - Web Speech API / Whisper voice input in the Copilot reply workspace, allowing executives to dictate natural spoken instructions that are converted into polished business emails.
6. **End-to-End Client-Side Envelope Encryption (E2EE):**
   - KMS-backed client-side envelope encryption for highly regulated compliance environments (HIPAA / SOC2).

---

# 32. Repository Structure

The repository currently follows a project-level organization similar to:

```text
EnterpriseAIMailOPs_MIPRO/
│
├── backend/
├── database/
├── docs/
├── frontend/
├── scripts/
├── storage/
│
├── .env
├── .env.example
├── .gitignore
├── docker-compose.yml
├── PROJECT_STATUS.md
├── README.md
└── requirements.txt
```

The exact internal structure of individual modules may evolve as the project implementation progresses.

---

# 33. Development Approach

MailOps AI is developed iteratively.

The general development flow is:

```text
Requirements
      ↓
Architecture
      ↓
Database
      ↓
Authentication
      ↓
Gmail Integration
      ↓
AI Intelligence
      ↓
Document Processing
      ↓
Search and Retrieval
      ↓
Action Relationships
      ↓
Frontend Integration
      ↓
Testing and Security
      ↓
Deployment
```

Implementation decisions should be made deliberately, and significant architectural changes should be documented.

---

## Current Project Status

For the actual implementation progress, current milestone, completed work, and next development steps, see:

`PROJECT_STATUS.md`

## License

This project is currently developed as a B.Tech academic and portfolio software engineering project.

License information may be added when the project is prepared for public distribution.