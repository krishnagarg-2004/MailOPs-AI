# MailOps AI — Comprehensive User Guide

Welcome to the **MailOps AI** User Guide. This guide covers everything you need to know to navigate, analyze, search, and operate your communication and work intelligence workflows.

---

## 📑 Table of Contents

1. [Quick Overview & Live Access](#1-quick-overview--live-access)
2. [Getting Started & Authentication](#2-getting-started--authentication)
   * [Live Google Account Sign-In](#live-google-account-sign-in)
   * [Instant Demo Persona (Offline / Sandbox)](#instant-demo-persona-offline--sandbox)
3. [Mailbox Synchronization & Navigation](#3-mailbox-synchronization--navigation)
   * [Initial Baseline Synchronization](#initial-baseline-synchronization)
   * [On-Demand "Load Older Emails (+50)"](#on-demand-load-older-emails-50)
   * [Real-Time Progress & Conflict-Free Sync](#real-time-progress--conflict-free-sync)
4. [The 3-Pane Work Intelligence Workspace](#4-the-3-pane-work-intelligence-workspace)
   * [Pane 1: Thread Navigator & Filter Modes](#pane-1-thread-navigator--filter-modes)
   * [Pane 2: Center Message Reader](#pane-2-center-message-reader)
   * [Pane 3: AI Intelligence & Copilot Inspector](#pane-3-ai-intelligence--copilot-inspector)
   * [Superhuman Keyboard Shortcuts](#superhuman-keyboard-shortcuts)
5. [AI Extraction & Work Intelligence](#5-ai-extraction--work-intelligence)
   * [Triggering Analysis](#triggering-analysis)
   * [Summary, Intent & Urgency Scoring](#summary-intent--urgency-scoring)
   * [Grounded Evidence Snippets](#grounded-evidence-snippets)
   * [Action Items & One-Click Google Calendar Sync](#action-items--one-click-google-calendar-sync)
   * [Decisions & Risks Tracking](#decisions--risks-tracking)
6. [AI Reply Copilot with Ghost-Text](#6-ai-reply-copilot-with-ghost-text)
   * [Tone Selection & Quick Intent Chips](#tone-selection--quick-intent-chips)
   * [Rich-Text Formatting Bar](#rich-text-formatting-bar)
   * [Inline Ghost-Text Autocomplete (`Tab`)](#inline-ghost-text-autocomplete-tab)
   * [Syncing to Gmail Drafts & Direct Sending](#syncing-to-gmail-drafts--direct-sending)
7. [Document Intelligence & OCR](#7-document-intelligence--ocr)
   * [Attachment Explorer & Category Filters](#attachment-explorer--category-filters)
   * [Automated PDF / Image OCR Extraction](#automated-pdf--image-ocr-extraction)
   * [Structured Invoice & Financial Extraction](#structured-invoice--financial-extraction)
   * [Downloading Extracted OCR Text](#downloading-extracted-ocr-text)
8. [Search & Grounded RAG Chat](#8-search--grounded-rag-chat)
   * [Semantic vs. Hybrid Search](#semantic-vs-hybrid-search)
   * [Asking Free-Form Questions with Citations](#asking-free-form-questions-with-citations)
   * [Re-Indexing Your Mailbox](#re-indexing-your-mailbox)
9. [Action Dependency Graph](#9-action-dependency-graph)
   * [Interactive Force-Directed Network](#interactive-force-directed-network)
   * [Critical Paths & Dependency Chains](#critical-paths--dependency-chains)
   * [Filtering Graph Nodes](#filtering-graph-nodes)
10. [Executive Digest & Reporting](#10-executive-digest--reporting)
    * [Generating Daily Operations Digests](#generating-daily-operations-digests)
    * [Exporting Reports (CSV & Markdown)](#exporting-reports-csv--markdown)
11. [Command Palette (`Ctrl+K`)](#11-command-palette-ctrlk)
12. [Troubleshooting & FAQ](#12-troubleshooting--faq)

---

## 1. Quick Overview & Live Access

MailOps AI turns your unstructured email inboxes into an actionable relational database and AI copilot.

* **Live Frontend:** [https://mailops-frontend.onrender.com](https://mailops-frontend.onrender.com)
* **Live Backend REST API:** [https://mailops-backend-67g3.onrender.com](https://mailops-backend-67g3.onrender.com)
* **API Documentation:** [https://mailops-backend-67g3.onrender.com/docs](https://mailops-backend-67g3.onrender.com/docs)
* **System Health Monitor:** [https://mailops-backend-67g3.onrender.com/health](https://mailops-backend-67g3.onrender.com/health)

---

## 2. Getting Started & Authentication

### Live Google Account Sign-In
1. Navigate to [https://mailops-frontend.onrender.com/login](https://mailops-frontend.onrender.com/login).
2. Click **Sign in with Google**.
3. Authorize Google OAuth permissions (read-only email access and optional compose scope for drafts/sending).
4. Once verified, you will be redirected straight to your unified Inbox Dashboard.

### Instant Demo Persona (Offline / Sandbox)
If you want to explore the application without connecting a personal Google account:
1. On the login screen, click **⚡ Explore Demo Mailbox** (or click **⚡ Seed Demo** in the top navigation header at any time).
2. The system will seed a realistic enterprise workspace with:
   * Multi-turn customer escalation threads.
   * Multi-page vendor invoices and cloud infrastructure statements.
   * Cross-functional action items, risks, and decision logs.
   * Interactive dependency graph connections.

---

## 3. Mailbox Synchronization & Navigation

The synchronization engine is built for speed, rate-limit safety, and continuous updates.

### Initial Baseline Synchronization
* When you connect a Gmail account, MailOps AI pulls the **50 most recent emails** in **~2 to 3 seconds**.
* Captures the baseline Google `historyId` watermark so that newly arriving emails are continuously tracked without re-fetching old messages.

### On-Demand "Load Older Emails (+50)"
Need older historical emails from months or years ago?
* Click **↓ Load Older Emails (+50)** (found in the sidebar card or directly at the bottom of the threads list).
* The engine queries Gmail for messages received prior to the earliest email in your database, downloading the next batch of 50 older emails.
* Your total synced message count automatically increments (e.g., 50 → 100 → 150).

### Real-Time Progress & Conflict-Free Sync
* Synchronization runs entirely in the background via asynchronous workers.
* The Server-Sent Events (SSE) stream publishes real-time progress (`Syncing email 13/50...`) directly to your UI.
* **Zero Conflict Popups:** All duplicate clicks or in-progress triggers are seamlessly debounced with subtle toast notifications. Your active email selection and draft editor are permanently preserved and never reset when a sync completes.

---

## 4. The 3-Pane Work Intelligence Workspace

Inspired by Superhuman, Linear, and Notion, the main dashboard (`/dashboard`) provides a responsive 3-pane layout:

```
┌─────────────────────────┬───────────────────────────────┬────────────────────────────────┐
│ Pane 1: Threads (3 cols)│ Pane 2: Message Reader (5 cols│ Pane 3: AI Copilot (4 cols)    │
│                         │                               │                                │
│ [Search threads...]     │ Re: Infrastructure Migration  │ [✨ Intelligence] [✉️ Copilot] │
│ [ALL] [URGENT] [ACTIONS]│ From: vendor@cloud.com        │                                │
│                         │                               │ Executive Summary              │
│ > Acme Corp Upgrade (1) │ Please confirm payment for    │ - Critical Net-30 invoice due. │
│   AWS Cloud Invoice (2) │ invoice #8892 due on Friday.  │                                │
│   Security Vulnerability│                               │ Extracted Actions:             │
│                         │ [✨ Analyze (a)] [✉️ Reply (r)] │ [ ] Review invoice ($14,850)   │
│ [↓ Load Older Emails]   │                               │     [Complete] [📅 Sync GCal]  │
└─────────────────────────┴───────────────────────────────┴────────────────────────────────┘
```

### Pane 1: Thread Navigator & Filter Modes
* **Search Filter:** Type keywords, sender names, or subject lines to filter matching threads in real time.
* **Quick Filter Pills:**
  * **ALL:** Full mailbox view.
  * **URGENT:** Only high-urgency or critical escalated emails.
  * **ACTIONS:** Threads with pending extracted action items.

### Pane 2: Center Message Reader
* Displays the complete email body with formatting, sender avatars, dates, and attachment indicators.
* Fast action toolbar at the top with quick triggers: `✨ Analyze (a)` and `✉️ Reply (r)`.

### Pane 3: AI Intelligence & Copilot Inspector
* Toggleable sidebar via the `Hide/Show AI Inspector (x)` button.
* Houses the deep AI intelligence card, action items, risks, and the rich reply copilot.

### Superhuman Keyboard Shortcuts
Press `?` anywhere in the dashboard to open the hotkey cheat sheet:

| Key | Action |
|---|---|
| `j` or `↓` | Navigate to next email thread |
| `k` or `↑` | Navigate to previous email thread |
| `a` | Trigger AI extraction on current message |
| `r` | Open AI Reply Draft Copilot |
| `x` | Toggle AI Inspector sidebar (expanded/collapsed) |
| `Tab` | Accept AI Ghost-Text autocomplete suggestion |
| `Ctrl + K` | Open Global Command Palette |
| `?` | Show / Hide Keyboard Shortcuts Modal |

---

## 5. AI Extraction & Work Intelligence

MailOps AI uses Google Gemini 2.5 Flash (with automatic deterministic fallback) to parse operational intelligence from communications.

### Triggering Analysis
* Select any email thread and click **✨ Analyze (a)** (or hit the `a` key).
* The engine analyzes the full message context, headers, and attachments in under 2 seconds.

### Summary, Intent & Urgency Scoring
* **Executive Summary:** A concise 2–3 sentence operational brief highlighting what happened, what is needed, and any business impact.
* **Intent & Sentiment:** Categorized into `URGENT_ACTION`, `FINANCIAL_REQUEST`, `DECISION_RECORD`, or `INFORMATIONAL`.
* **Urgency & Priority:** Ranked `CRITICAL`, `HIGH`, `MEDIUM`, or `LOW` with color-coded badges.

### Grounded Evidence Snippets
* MailOps AI eliminates hallucinations by providing exact **quoted evidence snippets** pulled directly from the email body to justify every extracted action, decision, and risk.

### Action Items & One-Click Google Calendar Sync
* Every detected task is extracted with an assignee and suggested due date.
* **Action Lifecycle:** Mark tasks as **Complete**, **Confirm**, or **Dismiss** with 1 click.
* **📅 Sync GCal:** Click the calendar button on any task to schedule it to Google Calendar, pre-populating the title, description, and deadline.

### Decisions & Risks Tracking
* **Decisions:** Logs critical agreements, vendor selections, or policy sign-offs for institutional memory.
* **Risks:** Highlights security risks, budget overruns, missed deadlines, or compliance exposures.

---

## 6. AI Reply Copilot with Ghost-Text

Craft context-aware, executive-ready replies in seconds.

### Tone Selection & Quick Intent Chips
* Choose between 3 professional tones:
  * **Professional:** Polished, diplomatic, and thorough.
  * **Concise:** Direct, efficient, and bulleted.
  * **Urgent:** High-priority, action-oriented, and time-sensitive.
* Click quick-intent chips (e.g. `+ Confirm Receipt`, `+ Request Timeline`, `+ Approve Invoice`) to guide the draft's objective.

### Rich-Text Formatting Bar
* Format your reply with Bold (`B`), Italic (`I`), Bullet Lists (`•`), Blockquotes (`"`), and Code Snippets (`<>`).

### Inline Ghost-Text Autocomplete (`Tab`)
* As you type or pause in the editor, the AI suggests the next phrase or sentence in gray ghost text.
* Press the **`Tab`** key to instantly accept the suggestion into your message.

### Syncing to Gmail Drafts & Direct Sending
* **Save as Gmail Draft:** Pushes the draft directly into your live Gmail drafts folder, preserving thread context (`In-Reply-To` and `References`).
* **Send via Gmail:** Sends the email directly through the Gmail API with your explicit confirmation.

---

## 7. Document Intelligence & OCR

Navigate to **Document OCR** (`/documents`) in the left navigation sidebar.

### Attachment Explorer & Category Filters
* Browse all attachments across your synchronized mailbox.
* Filter attachments by category: **Invoices**, **Contracts**, **PDFs**, or **Images**.

### Automated PDF / Image OCR Extraction
* Automatically extracts plain text from native PDFs and DOCX files.
* Falls back to **Tesseract OCR** for scanned images and flat PDF documents.
* Built-in security guards prevent zip-bomb exploits and path traversal attacks.

### Structured Invoice & Financial Extraction
* Automatically parses invoice numbers, vendor names, tax/GST amounts, due dates, and total financial amounts due.

### Downloading Extracted OCR Text
* Click **Download Parsed OCR Text** on any document card to download the clean plaintext version for your records or external analysis.

---

## 8. Search & Grounded RAG Chat

Navigate to **Search & RAG Chat** (`/search`) in the left sidebar.

### Semantic vs. Hybrid Search
* **Semantic Search:** Uses 768-dimensional vector embeddings (`text-embedding-004`) stored in `pgvector` to find emails by conceptual meaning (e.g. searching *"cloud hosting cost increases"* finds invoices mentioning *"AWS EC2 bill adjustments"*).
* **Hybrid Search:** Combines vector similarity with exact keyword matching (SQL `ILIKE`) using Reciprocal Rank Fusion (RRF) and cross-encoder re-ranking.

### Asking Free-Form Questions with Citations
* Use the **RAG Chat Assistant** to ask questions across your communications:
  * *"What is the total amount due across all unpaid invoices this month?"*
  * *"Who is responsible for the database migration rollback plan?"*
* Answers are grounded in your mailbox documents and provide clickable citations linking directly back to the source email or attachment.

### Re-Indexing Your Mailbox
* Click **⚡ Re-Index Mailbox** at any time to regenerate embeddings across all newly received messages and attachments.

---

## 9. Action Dependency Graph

Navigate to **Action Graph** (`/graph`) in the left sidebar.

### Interactive Force-Directed Network
* Visualizes your communications as an interactive knowledge graph.
* **Nodes:** Emails (Blue), Actions (Red/Crimson), Decisions (Purple), Invoices/Financials (Green), Risks (Amber).
* **Edges:** Dependencies, references, and blocking relationships.
* Pan, zoom, and drag nodes to explore relationship clusters.

### Critical Paths & Dependency Chains
* Click any node to open the BFS dependency drawer.
* See exactly which tasks are blocked, which dependencies must be completed first, and detect circular blocking chains.

### Filtering Graph Nodes
* Use the top category filter pills to isolate specific node types:
  * Show only **Actions & Blockers**.
  * Show only **Invoices & Financial Exposure**.
  * Highlight **Critical Path Chains**.
* Click **⚡ Auto-Generate Graph** to rebuild graph relationships across all analyzed emails.

---

## 10. Executive Digest & Reporting

### Generating Daily Operations Digests
* Click **📊 Executive Digest** in the top-right toolbar of the Inbox Dashboard.
* The modal computes an instant operational overview:
  * **Total Financial Exposure:** Aggregate sum of all pending invoices and payment requests.
  * **Pending Actions & Tasks:** Broken down by priority (Critical vs. Routine).
  * **Escalations & Identified Risks:** High-severity items requiring executive attention.

### Exporting Reports (CSV & Markdown)
* Click **Download CSV** for spreadsheet integration (Excel / Google Sheets).
* Click **Download Markdown** for formatted executive briefings (Slack / Notion / Confluence).

---

## 11. Command Palette (`Ctrl+K`)

Press `Ctrl + K` (or `Cmd + K` on macOS) anywhere in the application to open the quick-jump command palette:

* **Navigate Views:** Jump instantly to Inbox, Document OCR, Search RAG, or Action Graph.
* **Quick Actions:** Trigger **Seed Demo Data**, **Export Executive Digest**, or open **Keyboard Shortcuts**.
* **Filter by Typing:** Type commands with instant fuzzy matching.

---

## 12. Troubleshooting & FAQ

### Q: Why did initial sync only load 50 emails?
**A:** This is by design to ensure sub-3-second load times and avoid Google API rate limits. To load older emails, simply click the **"↓ Load Older Emails (+50)"** button at the bottom of the thread list as many times as you like.

### Q: Can I run this without Google OAuth credentials?
**A:** Yes! Click **"⚡ Seed Demo"** on the login screen. It will load a rich sandbox environment with realistic enterprise threads, invoices, and graph dependencies for offline testing.

### Q: Does the AI automatically send emails on my behalf?
**A:** **No.** MailOps AI strictly enforces human-in-the-loop control. The AI only generates drafts; sending requires your explicit confirmation and review.

### Q: What should I do if the server is sleeping on Render?
**A:** The application has a 24/7 UptimeRobot ping active. If you ever experience a slight delay on the first request, the container wakes up automatically within 20–30 seconds.

---

*MailOps AI — Enterprise Work Intelligence Platform.*
