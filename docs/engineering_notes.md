# Engineering Notes

## Architectural Guidelines

### 1. Modular Monolith Architecture
- The backend is organized into explicit domain modules within `backend/app/` (`api/`, `core/`, `domain/`, `schemas/`, `services/`, `repositories/`, `integrations/`, `ai/`, `documents/`, `search/`, `workers/`, `db/`).
- Modules communicate through clear Python service interfaces to enable future decomposition if necessary.

### 2. Security & Untrusted Inputs
- Email bodies, thread subject lines, and attachment contents are untrusted user data.
- All untrusted payloads must be delimited and sanitized before embedding or forwarding to LLM context prompts.
- OAuth refresh tokens must be encrypted before persistence.

### 3. Human-in-the-Loop Control
- AI assistant models propose draft responses and task extractions.
- Actions with external side effects (e.g. sending emails) strictly require manual human review and explicit user confirmation in the UI.

### 4. Direct SDK & Vector Strategy
- Primary LLM provider is Gemini via direct `google-genai` SDK.
- LangChain is excluded from structural application dependencies to avoid unnecessary complexity.
- PostgreSQL with `pgvector` serves as the primary relational and vector storage engine.
