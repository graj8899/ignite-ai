# ADR-0000: Agreed changes to the RAG v1 spec

Status: Accepted (2026-09-26)

The source spec is `docs/spec/rag-v1-spec.md`. The architecture is
`docs/architecture/overview.md`. Where this file and the spec disagree,
**this file wins**.

## How we work
- Developer (Gowtham) is learning full-stack AI engineering toward an FDE role.
- Teach-as-we-go: small steps; explain concepts before code; after each step,
  list changed files, explain decisions, and give commands to verify.
- One phase at a time. Never build Agents, MCP, tool calling or workflows in v1.

## Repository
- One git repo (`ignite-ai`), two apps: `apps/api` (FastAPI) and `apps/web` (Next.js).
- All backend modules live inside `apps/api/app/` (no repo-root `services/`).
- Frontend types are generated from FastAPI's OpenAPI schema (replaces `packages/shared-types`).
- Git + GitHub + GitHub Actions CI from day 1. One branch + PR per phase.

## Tooling
- Python 3.14 managed by **uv**; Node LTS with **npm**.
- Postgres + pgvector via Docker Compose (developer runs Docker on the Mac).
- Ruff for lint/format; pytest + httpx; Vitest + Testing Library.

## LLM
- OpenAI only in v1, behind `llm` and `embeddings` provider interfaces.
- Model names only from env vars (`OPENAI_MODEL`, `EMBEDDING_MODEL`).
- Start with `text-embedding-3-small`.

## Changes to the spec
1. Permission metadata is stored on documents/chunks from Phase 2 (enforced in Phase 3).
2. Auth in v1 = dev login switcher with seeded users, issuing a signed JWT; behind an interface for real SSO later.
3. Keyword retrieval = Postgres full-text search, named "keyword" (not "BM25").
4. Fusion = Reciprocal Rank Fusion (k=60).
5. Reranking: LLM reranker first; later measured against a local cross-encoder.
6. Add tables `document_versions` and `audit_log`.
7. Unauthorized document access returns 404, never 403 (hide existence).
8. Generate a fictional Ignite corpus (~80 docs) with deliberate permission traps.
9. `CLAUDE.md` at repo root; `docs/learning/phase-N.md` notes after each phase.
10. Request IDs from Phase 0 (cheap now, painful to add later).
