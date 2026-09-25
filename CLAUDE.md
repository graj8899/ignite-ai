# CLAUDE.md — Ignite RAG v1

## Project

Ignite is a fictional enterprise (20k+ employees, 50k+ documents across HR,
Engineering, Finance, Product, Support, Contracts). We are building a secure,
permission-aware RAG assistant that answers questions only from documents the
user is authorized to see, with backend-generated citations. It is a modular
monolith: FastAPI + Postgres/pgvector + Next.js. RAG v1 ends after Phase 7 and
is the foundation for later Agents, Tool Calling, MCP and workflow work.

**Learning goal:** the developer (Gowtham) is learning full-stack AI
engineering toward a Forward Deployed Engineer role. Teach as we go — the
point is understanding, not just working code.

## Source of truth

Precedence (highest first):

1. [docs/decisions/0000-agreed-changes-to-spec.md](docs/decisions/0000-agreed-changes-to-spec.md) — overrides the spec
2. [docs/architecture/overview.md](docs/architecture/overview.md) — architecture, flows, repo layout
3. [docs/spec/rag-v1-spec.md](docs/spec/rag-v1-spec.md) — original specification

If these docs conflict with a request, stop and ask.

## Working rules

- **One step at a time.** Do only the current step; don't jump ahead.
- **Explain concepts before coding.** Briefly explain the "why" and the
  underlying idea before writing code for it.
- **After each step, report:** changed files, key decisions (and
  alternatives rejected), and exact commands to verify.
- **Never implement Agents, MCP, tool calling or workflow automation in v1.**
- **Never commit secrets.** Keys live in `.env` (git-ignored); only
  `.env.example` with placeholder values is committed.
- **Ask before major architectural changes** — never silently swap
  Postgres/pgvector, FastAPI, Next.js or the provider interfaces.
- Prefer explicit code over framework magic; justify every new dependency.
- Check current official docs when pinning package or model versions.
- Record meaningful decisions as ADRs in `docs/decisions/`; write
  `docs/learning/phase-N.md` notes after each phase.

## Key constraints (from ADR-0000)

- No LangChain/LlamaIndex in the core pipeline; retrieval stays visible in code.
- Permission filtering happens **inside the SQL query** — unauthorized text
  never reaches the LLM.
- Unauthorized document access returns **404, never 403**.
- Citations are built by the backend from chunk metadata, never from
  model-written text/URLs.
- OpenAI only in v1, behind `llm` and `embeddings` interfaces; model names
  come only from env vars (`OPENAI_MODEL`, `EMBEDDING_MODEL`).
- Keyword retrieval = Postgres full-text search (called "keyword", not BM25);
  fusion = Reciprocal Rank Fusion (k=60).
- Every request gets a request ID (from Phase 0).
- Don't log full private documents, secrets or PII.

## Tooling

- Python 3.14 via **uv**; Ruff (lint + format); pytest + httpx
- Node LTS via **npm**; Next.js + TypeScript; Vitest + Testing Library
- Postgres + pgvector via Docker Compose; SQLAlchemy + Alembic
- Frontend types generated from FastAPI's OpenAPI schema
- GitHub Actions CI from day 1; one branch + PR per phase

## Repository layout (planned)

```
ignite-ai/
  CLAUDE.md                 # this file (exists)
  .gitignore                # (exists)
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
  docs/{spec,architecture,decisions,learning}   # spec/architecture/decisions exist
  .github/workflows/ci.yml
```

All backend modules live in `apps/api/app/` — no repo-root `services/` or
`packages/`.

## Commands

Placeholders — fill in as each step lands.

| Task | Command |
|---|---|
| Start Postgres + pgvector | `docker compose up -d` |
| Stop Postgres + pgvector | `docker compose down` (add `-v` to also delete data) |
| Run API (dev) | `cd apps/api && uv run fastapi dev app/main.py` |
| Run web (dev) | `TBD (Phase 1)` — `npm run dev` |
| Lint (Python) | `cd apps/api && uv run ruff check .` |
| Format (Python) | `cd apps/api && uv run ruff format .` |
| Lint (web) | `TBD` |
| Tests (API, unit only) | `cd apps/api && uv run pytest` |
| Tests (API, integration) | `cd apps/api && uv run pytest -m integration` (needs `docker compose up -d`) |
| Tests (web) | `TBD` — `npm test` |
| Run DB migrations | `cd apps/api && uv run alembic upgrade head` |
| Create a new migration | `cd apps/api && uv run alembic revision -m "description"` |
| DB migrations | `TBD` — `uv run alembic upgrade head` |
| Seed data | `TBD` |
| Run evaluation | `TBD (Phase 6)` |
| Generate frontend types | `TBD` |
