# MAILOPS AI (EnterpriseAIMailOPs_MIPRO) — CANONICAL PROJECT BIBLE

**Document Version**: 1.1
**Last Updated**: August 2026
**Status**: Approved Specification (Canonical Master Reference)

---

## 1. Project Identity

- **Working Title**: MAILOPS AI (`EnterpriseAIMailOPs_MIPRO`)
- **Alternative Titles Considered**: InboxIQ, MailMind AI, MailPilot AI
- **Project Classification**: B.Tech College Minor / Resume & Placement Portfolio Software Engineering Project
- **Domain Focus**: Enterprise Software, Artificial Intelligence, Natural Language Processing (NLP), Document Intelligence, Knowledge Retrieval, Workflow Automation
- **Canonical Product Definition**: MailOps AI is an AI-powered enterprise work-intelligence platform that connects organizational communication (emails) and business documents, understands their content and relationships, extracts actionable work information, provides contextual knowledge retrieval, identifies tasks, decisions, deadlines, and risks, assists with human-reviewed responses, and presents explainable intelligence through a unified workspace.

---

## 2. Executive Summary

MailOps AI bridges the gap between passive email/document consumption and proactive operational execution. Traditional email clients and basic AI chatbots handle message summaries in isolation; MailOps AI aggregates communication streams and unstructured documents into an interconnected knowledge and action layer. The platform highlights critical tasks, flags financial and operational risks, extracts structured key figures from invoices and contracts, models communication timelines via an Action Graph, and provides human-in-the-loop email composition assistance without taking unverified autonomous actions.

---

## 3. Problem Statement

Modern enterprise personnel suffer from severe operational friction caused by unstructured communication channels:
1. **Information Overload**: Heavy volumes of emails and attachments obscure urgent tasks.
2. **Context Fragmentation**: Critical decisions and commitments are scattered across disjointed threads and attachments.
3. **Manual Document Processing**: Manual inspection of invoices, receipts, and contracts for metadata extraction is error-prone and time-consuming.
4. **Missed Deadlines & Tasks**: Action items conveyed informally within email text lack automatic tracking.
5. **Inefficient Information Retrieval**: Keyword search fails to retrieve contextually or semantically related past discussions.
6. **Repetitive Draft Writing**: Re-typing routine responses consumes cognitive bandwidth.

---

## 4. Target Users

- **Operations Employees & Managers**: Tracking cross-departmental requests, status updates, and project bottlenecks.
- **Finance Personnel**: Processing vendor invoices, payment due dates, tax/GST values, and purchase order matches.
- **Legal & Compliance Teams**: Monitoring contract terms, clause variations, renewal dates, and obligation deadlines.
- **Individual Enterprise Professionals**: Organizing daily priorities, extracting action items, and drafting contextual responses.

---

## 5. Product Vision

To transform raw enterprise communication into an explainable, structured work-intelligence network where every incoming email or document automatically yields structured insights: *what happened, why it matters, what needs to be done next, where the supporting evidence is located, and how it links to existing enterprise knowledge.*

---

## 6. Core Product Concept

The platform is designed around five core pillars:
1. **Understand Before Acting**: Comprehensive parsing, chunking, and classification before presenting results.
2. **Explainable AI (XAI)**: Accompanying every classification or extraction with model confidence scores, rationale, and source evidence.
3. **Human-in-the-Loop Control**: AI proposes draft replies and task extractions; humans review, modify, and authorize consequential execution (e.g., sending emails).
4. **Action Graph Visualization**: Mapping communication events, tasks, participants, and documents as an interconnected flow.
5. **Unified Communication & Document Workspace**: Treating emails and attachments as co-equal sources of operational data.

---

## 7. Core Features

- **Google OAuth & Gmail Synchronization**: Secure account authentication and inbox indexing via Gmail API.
- **Email & Thread Intelligence**: Automatic summarization, intent classification, priority scoring, urgency detection, and sentiment analysis.
- **Action & Task Extraction**: Automatic identification of explicit requests, commitments, decisions, deadlines, and assigned owners.
- **Document & Attachment Intelligence**: Structured extraction from PDFs, DOCX, and images (invoices, contracts, receipts, POs) with fallback OCR.
- **Semantic & Knowledge Retrieval**: Vector-based semantic search across historical emails and extracted document chunks.
- **Explainable AI Insights**: Citation of exact text snippets, confidence percentages, and reasoning logs behind AI recommendations.
- **Action Graph Timeline**: Relationship view connecting emails, attachments, decisions, tasks, and deadlines.
- **Human-Reviewed Reply Composer**: AI draft generation based on conversation context with mandatory manual user approval.
- **Operational Intelligence Dashboard**: Unified view of daily priority emails, pending actions, document extractions, and analytics.

---

## 8. V1 Scope

The initial Version 1 system focuses strictly on:
- Single-user / Multi-user safe Google OAuth authentication.
- Read & draft access to Gmail API.
- Modular monolith backend architecture using Python, FastAPI, and PostgreSQL.
- Frontend interface built with React, TypeScript, Vite, and Tailwind CSS.
- Basic document processing for PDFs and common image formats with Tesseract OCR fallback.
- AI abstraction supporting Gemini as the primary provider.
- In-database vector retrieval using `pgvector` extension for PostgreSQL.
- Domain-model based Action Graph visualization.
- Complete unit, integration, API, security, and AI evaluation test structure.

---

## 9. Explicitly Out of Scope

To prevent scope creep, the following features are explicitly excluded from Version 1:
- Resume analysis, candidate scoring, and interview question generation.
- Autonomous email sending (sending without human review).
- Third-party chat integrations (Slack, Microsoft Teams, Discord).
- Non-Gmail email protocol clients (IMAP/POP3 direct servers) or Microsoft Outlook integration (deferred to V2).
- Dedicated graph databases (Neo4j) or dedicated vector databases (ChromaDB, Pinecone).
- Heavy agentic framework lock-in (LangChain is prohibited from becoming a core dependency).
- Microservices deployment infrastructure.

---

## 10. Functional Requirements

- **FR-AUTH-01**: Users must authenticate securely via Google OAuth 2.0.
- **FR-MAIL-01**: The system must fetch email threads, messages, metadata, and attachments via Gmail API.
- **FR-AI-01**: The system must analyze email messages and produce summaries, intent classifications, priority scores, and sentiment ratings.
- **FR-AI-02**: The system must extract action items, assigned owners, and explicit due dates from email threads.
- **FR-DOC-01**: The system must validate and extract text from attached PDF and image files, executing OCR when native text is absent.
- **FR-DOC-02**: The system must parse structured metadata from business documents (e.g., invoice total, GST, due date, contract clauses).
- **FR-RAG-01**: The system must index message/document text chunks into vector representations for semantic search.
- **FR-REPLY-01**: The system must generate draft replies using conversation context and present them for user editing and explicit manual dispatch.
- **FR-GRAPH-01**: The system must render visual timelines and dependency graphs connecting messages, documents, tasks, and deadlines.

---

## 11. Non-Functional Requirements

- **NFR-SEC-01**: OAuth tokens and API secrets must be encrypted at rest and never committed to source control.
- **NFR-SEC-02**: Email content and attachment text must be sanitized as untrusted input before processing to prevent prompt injection.
- **NFR-PERF-01**: API response times for read operations must remain under 200ms; long-running operations (Gmail sync, AI analysis, OCR) must run asynchronously in background jobs.
- **NFR-RELIABILITY-01**: Background workers must handle retries gracefully with exponential backoff on external API rate limits.
- **NFR-MAINTAINABILITY-01**: The backend must strictly follow clean architecture boundaries within a modular monolith structure.

---

## 12. System Architecture

MailOps AI uses a **Modular Monolith** architecture pattern for Version 1.

```
                   +--------------------------------+
                   | React + TypeScript + Vite UI   |
                   +--------------------------------+
                                   | (HTTP REST)
                                   v
                   +--------------------------------+
                   |      FastAPI Backend App       |
                   +--------------------------------+
                     |            |               |
                     v            v               v
           +-------------+  +------------+  +------------+
           | PostgreSQL  |  | Background |  | External   |
           | + pgvector  |  | Workers    |  | APIs       |
           +-------------+  +------------+  +------------+
                                              (Gmail/Gemini)
```

### Module Boundaries within `backend/app/`:
- `api/v1/`: HTTP route handlers and request validation.
- `core/`: Application settings, security, logging, error definitions.
- `domain/`: Pure domain entities and value objects.
- `schemas/`: Pydantic input/output validation models.
- `services/`: Core business logic coordinating domain models and repositories.
- `repositories/`: Database abstraction layer.
- `integrations/`: Third-party integration abstractions (Gmail client).
- `ai/`: Provider abstractions, prompt definitions, LLM clients.
- `documents/`: File parsing, text extraction, OCR engine interfaces.
- `search/`: Embedding generation and vector search handlers.
- `workers/`: Background job definitions and task queues.
- `db/`: Database session management and base models.

---

## 13. Domain Model

The conceptual domain consists of the following entity modules:

- **Identity**: `User`, `OAuthAccount`
- **Email**: `EmailThread`, `EmailMessage`, `Participant`, `Attachment`
- **Documents**: `Document`, `DocumentVersion`, `DocumentExtraction`
- **Intelligence**: `AIAnalysis`, `Classification`, `Entity`, `Recommendation`, `Evidence`
- **Actions**: `Action`, `Deadline`, `Decision`, `Risk`, `Relationship`
- **Knowledge**: `Chunk`, `Embedding`
- **Organization**: `Organization`, `Project`, `Client`
- **Infrastructure**: `ProcessingJob`, `AuditEvent`

---

## 14. Database Architecture

- **Primary Database Engine**: PostgreSQL.
- **Role**: Relational store of record for user profiles, OAuth tokens, email metadata, document extractions, action graph relationships, audit logs, and processing job queues.
- **Vector Search Engine**: `pgvector` extension embedded directly in PostgreSQL.
- **Design Rule**: No production migrations or table creation scripts during foundation milestone.

---

## 15. AI/ML Architecture

- **Primary Provider**: Gemini API (via direct `google-genai` / Official SDK).
- **Abstraction Layer**: `AIProvider` interface allowing seamless replacement with OpenAI, Anthropic, or local Ollama models in future phases.
- **Framework Constraint**: Direct SDK and custom prompt wrappers are preferred. LangChain is prohibited as a core structural dependency.
- **Structured Output**: AI responses strictly output JSON enforced by Pydantic models.
- **Prompt Injection Defense**: Untrusted user emails and attachments are wrapped in strict data delimiters (`<untrusted_content>`) with system prompts overriding payload instructions.

---

## 16. Gmail Integration

- **Authentication Protocol**: Google OAuth 2.0 with minimal required scopes (`gmail.readonly`, `gmail.compose`, `gmail.modify`).
- **Sync Mechanism**: Asynchronous background pull jobs syncing headers, body text, and attachments.
- **Drafting Workflow**: Draft creation in Gmail via API; sending requires explicit human authorization in the UI.

---

## 17. Document Intelligence

- **Supported Initial File Types**: PDF, PNG, JPEG, DOCX.
- **Processing Pipeline**: File validation -> Text extraction -> Fallback Tesseract OCR -> Normalization -> Chunking -> Metadata extraction -> Vector embedding indexing.
- **Extraction Models**:
  - *Invoices*: Vendor, Invoice #, Date, Due Date, Total Amount, Tax/GST, Payment Terms.
  - *Contracts*: Contracting Parties, Effective Date, Expiration Date, Key Obligations, Renewal Terms, Risk Clauses.

---

## 18. Search and Retrieval

- **Hybrid Search**: Structured filtering (by sender, date range, priority, tag) combined with vector similarity search.
- **Vector Retrieval**: Chunked document and message text embedded into `pgvector` columns in PostgreSQL.
- **Contextual RAG**: Retrieved chunks are injected into LLM context prompts alongside citation metadata for explainable answers.

---

## 19. Action Graph

- **Concept**: Visual and logical mapping of inter-entity relationships extracted from communication flow.
- **V1 Implementation**: Relational application mapping stored in PostgreSQL tables (`Relationship` domain entity) connecting `EmailThread` <-> `Document` <-> `Action` <-> `Deadline` <-> `Participant`.
- **Constraint**: Dedicated graph databases (e.g. Neo4j) are excluded from V1.

---

## 20. Human-in-the-Loop

- **Rule**: AI never performs high-stakes external mutations autonomously.
- **Workflows**:
  - *Replies*: AI generates draft -> Presented in UI -> User edits -> User explicitly clicks "Send Email".
  - *Tasks*: AI identifies action item -> Presented in UI -> User confirms/edits task before saving to active action list.

---

## 21. Security

- **Secrets Management**: Configuration loaded exclusively via environment variables (`.env`). No API keys or secrets in source code.
- **Multi-User Data Isolation**: Queries must strictly filter by `user_id`.
- **Data Protection**: OAuth refresh tokens encrypted before database storage.
- **Untrusted Input Handling**: All parsed emails and attachments treated as untrusted text payloads.

---

## 22. Testing and AI Evaluation

- **Test Infrastructure**: Pytest suite located in `backend/tests/`.
- **Test Categories**:
  - `unit/`: Core domain logic, utilities, configuration.
  - `integration/`: Database session, background workers.
  - `api/`: FastAPI endpoint testing via `httpx.AsyncClient`.
  - `security/`: Auth boundaries, prompt injection resistance tests.
  - `evaluation/`: AI output parsing, structured extraction accuracy checks.

---

## 23. Observability

- Structured JSON logging using standard Python `logging`.
- Audit logs stored in `AuditEvent` database table for security-critical actions (logins, email sends, setting changes).
- Background job processing logs tracking processing time and retry counts.

---

## 24. Deployment

- Containerization via Docker (`docker/Dockerfile` for backend and frontend).
- Local orchestration using `docker-compose`.
- Production target environments: Vercel (Frontend), Railway/Render/Cloud Run (Backend), Supabase/Neon PostgreSQL (Database).

---

## 25. Technology Stack

| Layer | Technology |
|---|---|
| **Language** | Python 3.14 (Backend), TypeScript (Frontend) |
| **Backend Framework** | FastAPI |
| **Frontend Framework** | React 18+ with Vite |
| **Styling** | Tailwind CSS |
| **Database** | PostgreSQL |
| **Vector Indexing** | `pgvector` |
| **Primary AI Model** | Gemini (Direct SDK) |
| **Authentication** | Google OAuth 2.0 |
| **OCR Engine** | Tesseract OCR |
| **Testing** | Pytest, Vitest |
| **Environment** | Python `.venv` (`py -3.14 -m venv .venv`) |

---

## 26. Development Roadmap

- **Milestone 1**: Foundation & Documentation setup (Current).
- **Milestone 2**: Core Authentication & Google OAuth setup.
- **Milestone 3**: Database schema, ORM setup & Alembic migrations.
- **Milestone 4**: Gmail API Integration & Message sync pipeline.
- **Milestone 5**: AI Core Engine & Intelligence extraction pipeline (Gemini).
- **Milestone 6**: Document Processing & OCR engine integration.
- **Milestone 7**: Semantic Search & RAG retrieval with `pgvector`.
- **Milestone 8**: Action Graph relationship layer & UI workspace.
- **Milestone 9**: Reply Drafting & Human-in-the-Loop approval workflows.
- **Milestone 10**: Testing, AI Evaluation, Security Auditing & Project Polish.

---

## 27. Engineering Rules

1. **No Speculative Code**: Build only what is specified for the current milestone.
2. **No Unjustified Dependencies**: Every package must be explicitly approved.
3. **No Unsafe Execution**: Untrusted email payloads must never be executed as instructions.
4. **Preserve Compatibility**: Keep `EnterpriseAIMailOPs_MIPRO.txt` in sync with `PROJECT_BIBLE.md`.
5. **Clean Code**: Use explicit type hints, Pydantic validation, and structured docstrings.

---

## 28. Git Workflow

- **Branching**: `main` branch for stable releases; feature branches for milestones.
- **Commits**: Small, atomic conventional commits (`feat:`, `fix:`, `docs:`, `chore:`).
- **Security**: Pre-commit verification for clean diffs, no stray secrets, and passing tests.

---

## 29. Documentation Rules

- Maintain all architectural decisions in `docs/decision_log.md`.
- Keep current status tracked in `PROJECT_STATUS.md`.
- Ensure technical details in `docs/` reflect actual implementation state, not future concepts.

---

## 30. Risks & Mitigation

| Risk | Impact | Mitigation Strategy |
|---|---|---|
| **Scope Creep** | Project incompleteness | Strict adherence to V1 scope boundaries and explicit out-of-scope list. |
| **External Rate Limits** | Sync delays / failures | Asynchronous background processing with exponential backoff retries. |
| **Prompt Injection** | AI security breach | Delimiter isolation (`<untrusted_content>`) and output validation via Pydantic schemas. |
| **High Dependency Complexity** | Maintenance pain | Avoid heavy frameworks (LangChain); stick to native SDKs and lightweight tools. |

---

## 31. Future Improvements (Post-V1)

- Expansion to Microsoft Outlook, Microsoft Teams, and Slack integration.
- Multi-agent AI orchestration.
- Advanced invoice matching against purchase orders.
- Meeting transcript parsing and calendar integration.

---

## 32. Architecture Decision Record / Decisions

- **ADR-001**: Adopt Modular Monolith for V1 instead of Microservices.
- **ADR-002**: Use `pgvector` inside PostgreSQL for vector retrieval instead of standalone ChromaDB.
- **ADR-003**: Use direct Gemini SDK instead of LangChain for AI integration.
- **ADR-004**: Model Action Graph using domain entity relationships in PostgreSQL rather than dedicated graph database (Neo4j).
- **ADR-005**: Standardize on Python 3.14 and `py -3.14 -m venv .venv` for local virtual environment execution.

---

## 33. Change Log

- **v1.0** (August 2026): Initial Project Bible created (`EnterpriseAIMailOPs_MIPRO.txt`).
- **v1.1** (August 2026): Structured `PROJECT_BIBLE.md` created as canonical maintained specification reflecting approved V1 modular monolith architecture, `pgvector`, direct Gemini SDK usage, and Python 3.14 virtual environment.
