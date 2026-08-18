# Live & Manual Environment Smoke-Test Checklist

This checklist defines manual verification steps to validate **MailOps AI** in a live environment connected to real Google OAuth credentials, live Gemini API endpoints, and live Gmail mailboxes.

> [!NOTE]
> Automated tests in CI/CD run offline using mock/fake providers (`MockAIProvider`, `MockEmbeddingProvider`). This checklist is used for manual staging/production release validation.

---

## 1. Google OAuth 2.0 & Authentication (`/auth`)

- [ ] **Step 1.1: Standard OAuth Login**:
  - Navigate to `http://localhost:5173/login`.
  - Click **Sign in with Google**.
  - Verify redirection to Google consent screen requesting standard scopes (`openid`, `email`, `profile`, `gmail.readonly`).
  - Grant consent and verify redirection to `/dashboard`.
- [ ] **Step 1.2: Session Security Verification**:
  - Open browser DevTools -> Storage -> Cookies.
  - Verify `mailops_session` HttpOnly, SameSite=Lax cookie is present.
  - Refresh `/api/v1/auth/me` and verify user profile (`id`, `email`, `full_name`).
- [ ] **Step 1.3: Logout Revocation**:
  - Click **Logout**.
  - Verify session cookie is deleted and unauthenticated access returns `401 Unauthorized`.

---

## 2. Gmail API Synchronization (`/gmail`)

- [ ] **Step 2.1: Initial Synchronization**:
  - Log in and click **Sync Mailbox**.
  - Verify `POST /api/v1/gmail/sync` executes and captures baseline `historyId`.
  - Check `/api/v1/gmail/threads` and verify threads display subject, snippet, and message counts.
- [ ] **Step 2.2: Attachment Storage Verification**:
  - Verify attachments under 10 MB are downloaded to `storage/attachments/{user_id}/`.
  - Verify attachments exceeding 10 MB trigger log warnings and are skipped.

---

## 3. AI Core Engine & Gemini Pipeline (`/ai`)

- [ ] **Step 3.1: Live Gemini Extraction**:
  - Set `AI_PROVIDER_TYPE=gemini` and supply valid `GEMINI_API_KEY` in `.env`.
  - Trigger analysis for a work request email: `POST /api/v1/ai/analyze/message/{id}`.
  - Verify response contains structured summary, intent, priority, sentiment, and `actions` array.
- [ ] **Step 3.2: Evidence & Provenance Verification**:
  - Inspect `evidence_snippet` for extracted actions.
  - Verify snippet matches exact text from source email body (`is_evidence_valid=True`).

---

## 4. Document Intelligence & OCR Engine (`/documents`)

- [ ] **Step 4.1: Multi-Format Parsing**:
  - Process PDF invoice attachment: `POST /api/v1/documents/process/{attachment_id}`.
  - Verify page boundary markers (`--- [Page 1] ---`) in extracted text.
- [ ] **Step 4.2: Structured Invoice / Contract AI Analysis**:
  - Call `POST /api/v1/documents/analyze-business-doc/{attachment_id}`.
  - Verify structured `InvoiceExtractionSchema` (invoice number, total amount, GST, due date, vendor).

---

## 5. Semantic Search & RAG Engine (`/search`)

- [ ] **Step 5.1: pgvector Embedding Generation**:
  - Call `POST /api/v1/search/reindex` to chunk and embed user messages.
  - Verify 768-dimension vectors are stored in `vector_embeddings` table.
- [ ] **Step 5.2: Grounded RAG Chat**:
  - Submit query: `POST /api/v1/search/rag-query` with `"What is the due date for Invoice #9901?"`.
  - Verify AI response includes grounded answer and explicit citations (`[Source: Invoice_9901.pdf, Page 1]`).

---

## 6. Action Graph & Relationship Layer (`/graph`)

- [ ] **Step 6.1: Graph Network Visual**:
  - Call `GET /api/v1/graph/visual`.
  - Open `ActionGraphWidget.tsx` in UI and verify nodes (`EMAIL_MESSAGE`, `ACTION_ITEM`, `INVOICE`) and directed edges (`DEPENDS_ON`, `BLOCKED_BY`).
- [ ] **Step 6.2: BFS Dependency Resolution**:
  - Call `GET /api/v1/graph/dependencies/{action_id}`.
  - Verify dependency blocking tree resolves up to `GRAPH_MAX_TRAVERSAL_DEPTH=10`.

---

## 7. Human-in-the-Loop Reply Drafting & Gmail Sync (`/reply-drafts`)

- [ ] **Step 7.1: Local AI Draft Generation**:
  - Call `POST /api/v1/reply-drafts/generate` with `tone="PROFESSIONAL"`.
  - **INVARIANT VERIFICATION**: Confirm draft persists locally in `reply_drafts` with `status="DRAFTED"` and NO email is sent.
- [ ] **Step 7.2: Human-in-the-Loop Editing**:
  - Edit subject and body text via `PUT /api/v1/reply-drafts/{id}`.
  - Verify status transitions to `"EDITED"`.
- [ ] **Step 7.3: Incremental OAuth Consent (`gmail.compose`)**:
  - Attempt `POST /api/v1/reply-drafts/{id}/sync-gmail` without `gmail.compose` scope.
  - Verify HTTP `403 Forbidden` response: `"Gmail compose permissions are required to sync/send email"`.
  - Click **Authorize Compose Scope** (`/api/v1/auth/google/authorize-compose`).
  - Grant compose consent on Google consent screen.
- [ ] **Step 7.4: Live Gmail Draft Synchronization**:
  - Call `POST /api/v1/reply-drafts/{id}/sync-gmail`.
  - Open Gmail web client (`mail.google.com`) and inspect Drafts folder.
  - Verify draft subject, body text, recipient, and `In-Reply-To`/`References` threading headers.
- [ ] **Step 7.5: Explicit Human-Approved Sending**:
  - Call `POST /api/v1/reply-drafts/{id}/send`.
  - Verify email is delivered to recipient mailbox with thread history preserved and status updated to `"SENT"`.
