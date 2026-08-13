# System Architecture Overview

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
