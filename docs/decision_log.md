# Decision Log (Architecture Decision Records)

## ADR-001: Modular Monolith Architecture for V1
- **Status**: Approved
- **Context**: Deciding between microservices and monolith architecture for initial release.
- **Decision**: Adopt a Modular Monolith backend structure in FastAPI with clean module separation (`api/`, `core/`, `domain/`, `schemas/`, `services/`, `repositories/`, `integrations/`, `ai/`, `documents/`, `search/`, `workers/`, `db/`).
- **Rationale**: Reduces operational complexity for a college portfolio project while retaining clean software boundaries for future microservice extraction.

## ADR-002: PostgreSQL + `pgvector` for Vector Retrieval
- **Status**: Approved
- **Context**: Selecting storage layer for structured data and vector embeddings.
- **Decision**: Use PostgreSQL for structured relational storage and enable `pgvector` extension for semantic retrieval.
- **Rationale**: Eliminates the operational overhead of running a separate vector database (e.g. ChromaDB) in V1.

## ADR-003: Direct Gemini SDK Integration
- **Status**: Approved
- **Context**: Choosing AI integration mechanism.
- **Decision**: Integrate Gemini API directly using the official `google-genai` Python SDK via custom provider interfaces.
- **Rationale**: Avoids framework lock-in and debugging friction associated with heavy agentic libraries like LangChain.

## ADR-004: Domain-Model Relational Action Graph
- **Status**: Approved
- **Context**: Visualizing communication timelines and entity relationships.
- **Decision**: Model the Action Graph as relational domain links in PostgreSQL (`Relationship` entities) rendered via React frontend visualization.
- **Rationale**: Provides clear task and timeline representation without introducing Neo4j or dedicated graph database infrastructure.

## ADR-005: Python 3.14 Environment Specification
- **Status**: Approved
- **Context**: Virtual environment configuration.
- **Decision**: Standardize on Python 3.14 and `py -3.14 -m venv .venv` execution launcher for local virtual environments.
- **Rationale**: Ensures runtime consistency across team environments.

## ADR-006: Database Foundation Architecture & Token Storage Security Boundary
- **Status**: Approved
- **Context**: Designing database integration, session scope, ORM models, and OAuth credential storage for Milestone 2.
- **Decision**:
  1. Standardize on PostgreSQL with `pgvector/pgvector:pg16` Docker image, SQLAlchemy 2.0 ORM, `psycopg` (v3) driver, and Alembic version control.
  2. Implement request-scoped database session management via FastAPI `get_db()` generator with explicit cleanup.
  3. Model identity using `User` and `OAuthAccount` tables connected by a one-to-many relationship (`User.oauth_accounts`) with cascade deletion.
  4. Establish OAuth credential storage boundary on `OAuthAccount` via nullable text columns (`encrypted_access_token`, `encrypted_refresh_token`). Plaintext tokens MUST NEVER be stored in source control or unencrypted database columns. Application-level symmetric key encryption will be attached during Milestone 3 OAuth implementation.
- **Rationale**: Guarantees clean architecture separation, strict data integrity, automated migration tracking, and security compliance before implementing external authentication flows.

## ADR-007: Fey Web Luxury Dark Mode Design System Adoption
- **Status**: Approved
- **Context**: Upgrading MailOps UI from functional dark mode with emojis and flat black backgrounds to an enterprise-grade luxury fintech/SaaS standard matching Fey Web (`fey.com` / Mobbin).
- **Decision**:
  1. Adopt layered obsidian backgrounds (`#000000` / `#08080a` canvas with `#0e0e12` / `#0f0f12` elevated card surfaces and inset top highlights `inset 0 1px 0 0 rgba(255,255,255,0.05)`).
  2. Replace all emojis with Lucide SVG vector icons (`Inbox`, `FileText`, `Search`, `Network`, `Sparkles`, `Command`, `BarChart3`).
  3. Use hairline border tokens (`border-white/[0.06]` to `border-white/[0.08]`) that elevate to `border-white/[0.14]` on hover.
  4. Enforce strict black/zinc/red color palette with high-contrast typography and tabular monospace numbers.
- **Rationale**: Elevates MailOps to the benchmark visual quality of modern enterprise SaaS applications while maintaining 100% test suite and WCAG contrast compliance.
