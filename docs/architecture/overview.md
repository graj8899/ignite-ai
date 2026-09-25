# Ignite RAG v1 — Architecture Overview

Status: Accepted (2026-09-26)

## 1. The big picture

Ignite is a *modular monolith*: one backend app (FastAPI) with clearly separated
modules, one database (Postgres + pgvector), one frontend (Next.js).
Modules talk through plain Python function calls, not network calls, so it is
easy to read, debug and learn from. Boundaries are kept clean so a module can
be extracted into its own service later if scale demands it.

```mermaid
flowchart LR
  UI[Next.js web app] -->|HTTP JSON| API[FastAPI routes]
  API --> AUTH[auth]
  API --> RAG[rag orchestrator]
  API --> ING[ingestion]
  RAG --> RET[retrieval]
  RAG --> LLM[llm provider]
  RAG --> CIT[citations]
  ING --> EMB[embeddings provider]
  RET --> EMB
  RET --> DB[(Postgres + pgvector)]
  ING --> DB
  CIT --> DB
  RAG --> OBS[observability]
  OBS --> DB
  LLM --> OAI[OpenAI Responses API]
  EMB --> OAIE[OpenAI Embeddings API]
```

## 2. Flow A — Ingesting a document (Phase 2)

```mermaid
flowchart LR
  U[Upload file + permissions] --> H[checksum]
  H -->|unchanged| SKIP[skip: idempotent]
  H -->|new or changed| P[parse PDF/MD/TXT]
  P --> C[clean]
  C --> K[chunk by section/page]
  K --> E[embed chunks]
  E --> W[write new version as INACTIVE]
  W --> S[one transaction: activate new, deactivate old]
```

Key rules:
- Each document is chunked on its own (never glued to other documents).
- Every chunk carries: document_id, version, page/section, source, permissions.
- Same file uploaded twice => same checksum => nothing happens (idempotent).
- If anything fails, the old version stays live and the job records the error.

## 3. Flow B — Answering a question (Phases 1, 3, 4, 5)

```mermaid
sequenceDiagram
  participant U as User
  participant API as FastAPI
  participant R as Retrieval
  participant DB as Postgres
  participant L as OpenAI
  U->>API: POST /api/chat {question}
  API->>API: authenticate, validate, create request_id
  API->>R: retrieve(question, user)
  R->>L: embed question
  R->>DB: vector search WITH permission filter
  R->>DB: keyword search WITH permission filter
  R->>R: merge (Reciprocal Rank Fusion) + rerank
  R-->>API: top-K authorized chunks
  API->>L: versioned prompt + numbered sources [S1..Sn]
  L-->>API: {answer, cited_source_ids, insufficient_evidence}
  API->>DB: build citations from real chunk metadata
  API->>DB: record run: timings, tokens, cost, scores
  API-->>U: answer + citations + request_id
```

The most important security idea: **permission filtering happens inside the
database query**, so unauthorized text never reaches the LLM. The model cannot
leak what it never sees.

## 4. Backend modules (all inside `apps/api`)

| Module | Responsibility |
|---|---|
| routes | HTTP only; no business logic |
| auth | who is the user; what can they see (dev login switcher in v1) |
| ingestion | parse, clean, chunk, embed, publish versions |
| retrieval | vector + keyword search, fusion, reranking |
| rag | build bounded context, call LLM, enforce grounded answers |
| citations | turn cited source ids into real document metadata |
| evaluation | golden dataset runner + metrics |
| observability | request ids, stage timings, tokens, cost |
| llm / embeddings | provider interfaces + OpenAI implementation |
| repositories | all SQL / database access |

## 5. Data model

Tables from the spec, plus two additions (marked +):
users, departments, user_departments, documents, **+document_versions**,
document_permissions, chunks, ingestion_jobs, evaluation_cases, rag_runs,
retrieval_results, **+audit_log**.

## 6. Repository layout

```
ignite-ai/
  CLAUDE.md                 # project rules for every Claude session
  docker-compose.yml        # Postgres + pgvector
  .env.example
  apps/
    api/                    # FastAPI backend (uv project)
      app/{routes,auth,ingestion,retrieval,rag,citations,
           evaluation,observability,llm,repositories,models}
      migrations/           # Alembic
      tests/{unit,integration,evaluation}
    web/                    # Next.js frontend
  data/{sample-documents,eval}
  docs/{architecture,decisions,learning}
  .github/workflows/ci.yml
```

## 7. Where each thing runs (local dev)

| Thing | Runs on | Who starts it |
|---|---|---|
| Postgres + pgvector | Docker Desktop on your Mac | you: `docker compose up -d` |
| FastAPI | your Mac terminal | you: `uv run fastapi dev` |
| Next.js | your Mac terminal | you: `npm run dev` |
| Unit tests / linting | Claude's sandbox on your Mac, and your terminal | both |
| Integration tests (need DB) | your Mac terminal | you, and GitHub CI |

## 8. Decisions to record as ADRs

1. Modular monolith, single backend app.
2. Postgres + pgvector for both relational and vector data.
3. Permission filter inside SQL (pre-filter), 404 for unauthorized.
4. Postgres full-text search as "keyword" retrieval (not true BM25).
5. Reciprocal Rank Fusion to merge results.
6. LLM reranker first, measured against a local cross-encoder later.
7. Citations built by the backend from source ids, never model-written URLs.
8. Dev login switcher with seeded users instead of real SSO.
9. OpenAI behind provider interfaces; models set via env vars.
10. uv for Python, npm for Node, GitHub Actions CI from day 1.
