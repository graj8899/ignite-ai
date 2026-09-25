**RAG v1 — Claude / VS Code Build Specification**

Purpose: build a production-minded RAG system that becomes the
foundation for later Agents, Tool Calling, MCP, workflow automation and
FDE system design.

This document is the source specification for the first implementation
stage of the Ignite project. Use it with Claude in VS Code. Claude
should first validate and explain the architecture, then implement
incrementally, run tests, and explain important decisions. Do not
generate the entire codebase blindly in one step.

# 1. Project Context

Ignite is a fictional enterprise platform with internal knowledge spread
across HR, Engineering, Finance, Product, Customer Support, Contracts
and operational documentation. Employees need a secure natural-language
assistant that can answer questions from authorized company information
and provide trustworthy citations.

Initial scale assumptions:

- 20,000+ employees/users.

- 50,000+ documents across several departments.

- Documents can be updated regularly.

- Approximately 8,000 questions/day initially, with future growth.

- Documents contain different permission levels.

- The system must be designed so enterprise integrations and agentic
  actions can be added later.

# 2. RAG v1 Scope

RAG v1 ends after Phase 7. Do NOT implement Agents, MCP, autonomous
actions, workflow automation, or production AWS deployment yet.

## Phase 1 — Basic RAG

Question → query embedding → vector retrieval → context → LLM → answer.

## Phase 2 — Ingestion

Upload/ingest documents → parse → clean → chunk → metadata → embeddings
→ PostgreSQL/pgvector.

## Phase 3 — Permission-aware RAG

Authenticate user, enforce authorization during retrieval, prevent
unauthorized data from entering context.

## Phase 4 — Retrieval quality

Hybrid semantic + keyword retrieval, metadata filtering, reranking,
top-K experiments.

## Phase 5 — Citations + freshness

Backend-generated citations from source metadata, document versioning,
update/deactivation flow.

## Phase 6 — Evaluation

Golden dataset, retrieval metrics, answer quality, groundedness,
citation correctness, regression tests.

## Phase 7 — Observability

Request IDs/traces, latency breakdown, token/cost tracking, retrieval
diagnostics, errors, model/prompt versions.

# 3. Explicit Non-Goals for RAG v1

- No autonomous agents.

- No MCP implementation.

- No direct LLM access to databases or enterprise APIs.

- No workflow automation.

- No Kubernetes.

- No multi-agent architecture.

- No fine-tuning.

- No LangChain/LlamaIndex as a black box for the core RAG pipeline. Core
  retrieval should be understandable and visible in application code.

- No premature microservice decomposition.

# 4. Recommended Technology Stack

| Area                 | Technology                                                  | Purpose                                                                                         |
|----------------------|-------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| Frontend             | Next.js + React + TypeScript                                | Chat UI, citations, document/admin views, evaluation/observability views.                       |
| Backend              | Python 3.14 + FastAPI                                       | API layer and core AI/RAG orchestration. Python 3.14.7 is the current 3.14 maintenance release. |
| Validation           | Pydantic                                                    | Request/response/domain validation.                                                             |
| Database             | PostgreSQL + pgvector                                       | Relational data + vector search in one system.                                                  |
| LLM                  | OpenAI API using the Responses API/current Python SDK       | Generation, structured outputs, future tool calling.                                            |
| Embeddings           | Provider abstraction around an embedding API                | Keep embedding provider/model replaceable.                                                      |
| ORM/data access      | SQLAlchemy + Alembic                                        | Explicit schema, migrations and database access.                                                |
| Testing              | pytest + httpx                                              | Unit/integration/API tests.                                                                     |
| Frontend testing     | Vitest + Testing Library                                    | Component/UI tests.                                                                             |
| Local infrastructure | Docker Compose                                              | PostgreSQL/pgvector and supporting services.                                                    |
| Formatting/linting   | Ruff + formatter; TypeScript ESLint/Prettier as appropriate | Consistent code quality.                                                                        |
| Future cache         | Redis                                                       | Reserved extension point; do not make it mandatory for RAG v1.                                  |
| Future queue         | AWS SQS / equivalent                                        | Reserved for incremental ingestion and enterprise events.                                       |
| Future event routing | AWS EventBridge / equivalent                                | Reserved for event-driven integrations.                                                         |
| Future MCP           | Official MCP TypeScript SDK v2                              | Reserved for the later MCP phase.                                                               |

Current-stack note: Python 3.14.7 is the current 3.14 maintenance
release. OpenAI's current API documentation supports Responses API tools
and function calling. MCP's official TypeScript SDK v2 is the current
stable 2026 line. Use current official documentation when exact
package/model versions are pinned.

# 5. Architecture

Use a modular monolith initially. Keep boundaries clean enough that
components can later be extracted if scale requires it.

High-level flow:  
Next.js UI → FastAPI → Query/AI service → Retrieval service →
PostgreSQL/pgvector → Context builder → OpenAI Responses API → Answer +
validated citations.

Ingestion flow:  
Document source/upload → parser → cleaner → chunker →
metadata/permissions → embedding service → PostgreSQL/pgvector.

Later extension points:  
Document change event → queue → worker → ingestion pipeline; Agent →
tools → enterprise systems; Agent → MCP client → MCP servers.

# 6. Suggested Repository Structure

ignite-ai/  
apps/  
web/ \# Next.js frontend  
api/ \# FastAPI backend  
services/  
ingestion/ \# Ingestion orchestration (can remain inside API
initially)  
retrieval/ \# Retrieval and reranking logic  
evaluation/ \# Evaluation runner  
packages/  
shared-types/ \# Shared API/domain types where useful  
infra/  
docker/  
compose/  
migrations/  
data/  
sample-documents/  
eval/  
tests/  
unit/  
integration/  
evaluation/  
docs/  
architecture/  
decisions/  
.env.example  
docker-compose.yml  
README.md

# 7. Backend Module Boundaries

- api/routes — HTTP endpoints only; keep business logic out of route
  handlers.

- services/ingestion — parse, clean, chunk, metadata, embedding
  orchestration.

- services/retrieval — query embedding, filters, vector/keyword
  retrieval, reranking.

- services/rag — context construction and answer generation.

- services/citations — construct citations from trusted chunk/document
  metadata.

- services/auth — authentication/authorization boundary.

- services/evaluation — golden-set execution and metric calculation.

- services/observability — request IDs, tracing, metrics, token/cost
  recording.

- repositories — database access.

- models/schemas — SQLAlchemy models and Pydantic schemas.

- llm — provider abstraction and OpenAI implementation.

# 8. Core Data Model

- users: id, name, email, role, status, created_at.

- departments: id, name.

- user_departments: user_id, department_id.

- documents: id, title, source, owner, department, version, checksum,
  status, created_at, updated_at.

- document_permissions: document_id, subject/user/role/department,
  access_type.

- chunks: id, document_id, version, content, page, section, metadata,
  embedding, active.

- ingestion_jobs: id, document_id, version, status, error, started_at,
  completed_at.

- evaluation_cases: id, question, expected_answer, expected_sources,
  metadata.

- rag_runs: request_id, user_id, query, model, prompt_version,
  retrieval_count, latency fields, input/output tokens, estimated cost,
  status.

- retrieval_results: request_id, chunk_id, rank, retrieval_method,
  score, rerank_score.

Do not expose unauthorized document metadata through search results,
citations, error messages, autocomplete or UI.

# 9. API Requirements

| Endpoint                         | Purpose                                                                                      |
|----------------------------------|----------------------------------------------------------------------------------------------|
| POST /api/chat                   | Ask a question. Return answer, citations, request_id and relevant diagnostics-safe metadata. |
| POST /api/documents              | Upload/register a document for ingestion.                                                    |
| GET /api/documents/{id}          | Document metadata/status; authorization required.                                            |
| POST /api/documents/{id}/reindex | Reprocess an authorized document/version.                                                    |
| GET /api/health                  | Basic health check.                                                                          |
| GET /api/readiness               | Readiness for DB/required dependencies.                                                      |
| POST /api/evaluations/run        | Run evaluation dataset; development/admin use only.                                          |

# 10. RAG Query Pipeline

1.  Authenticate user.

2.  Validate query.

3.  Create request/trace ID.

4.  Generate query embedding.

5.  Apply permission filters before returning candidates.

6.  Run vector retrieval.

7.  Run keyword/BM25 retrieval where configured.

8.  Combine candidates.

9.  Rerank candidates.

10. Construct bounded context from authorized chunks.

11. Call the LLM with a versioned system prompt.

12. Require the model to answer from supplied context and explicitly
    state when evidence is insufficient.

13. Construct citations from backend metadata, not from untrusted
    model-generated URLs.

14. Record safe observability metadata.

15. Return answer + citations + request ID.

# 11. Ingestion Requirements

- Support PDF and text/Markdown initially; design parser interface so
  DOCX/HTML can be added later.

- Never concatenate unrelated documents before chunking.

- Preserve document_id, version, page/section, source, timestamps and
  permissions on every chunk.

- Use deterministic document checksums/version IDs to detect unchanged
  documents.

- New versions must not leave stale chunks active.

- Failed ingestion must produce a clear job status and error without
  partially publishing an invalid version.

- Make ingestion idempotent.

# 12. Retrieval Requirements

- Start with vector similarity search.

- Add keyword/BM25 retrieval.

- Combine results using a clearly documented strategy such as Reciprocal
  Rank Fusion.

- Add reranking after candidate retrieval.

- Support metadata filters.

- Make top-K, candidate count and reranking parameters configurable.

- Record retrieval scores/ranks for evaluation and debugging.

- Do not allow the LLM to bypass permission filtering.

# 13. Citation Requirements

- Every factual answer should be traceable to retrieved source chunks
  where possible.

- Citation metadata must come from the backend/database.

- Include document title, page/section when available, and stable
  document identifier.

- Do not fabricate citations.

- If evidence is insufficient, the assistant should say so rather than
  inventing an answer.

# 14. Evaluation Requirements

Create at least 30–50 evaluation questions covering easy, ambiguous,
permission-sensitive and failure cases.

- Retrieval recall@K.

- Retrieval precision/relevance.

- Answer correctness.

- Groundedness/faithfulness.

- Citation correctness.

- Permission leakage tests.

- No-answer/insufficient-context behavior.

- Latency and cost per request.

- Regression comparison between versions.

# 15. Observability Requirements

- Every request gets a request_id/trace_id.

- Record stage timings: embedding, retrieval, reranking, LLM, total.

- Record input/output token usage where available.

- Estimate cost per request.

- Record model and prompt version.

- Record retrieval count and scores.

- Record error type and stage.

- Do not blindly log complete private documents, sensitive prompts,
  secrets or PII.

- Provide enough metadata to reproduce/debug retrieval failures.

# 16. Security Requirements

- Never commit API keys.

- Use .env locally and a secret manager in production later.

- Enforce authorization server-side.

- Treat retrieved document text as untrusted input to the LLM.

- Design for prompt-injection resistance even though the full
  AI-security phase comes later.

- Keep tool/action interfaces out of RAG v1.

- Prevent cross-user/cross-department retrieval leakage.

- Audit permission-sensitive access.

# 17. Testing Strategy

- Unit tests: chunking, metadata, permission filters, retrieval ranking,
  citation construction, schema validation.

- Integration tests: PostgreSQL/pgvector, ingestion pipeline, API
  endpoints, authentication/authorization.

- Evaluation tests: golden dataset regression.

- Security tests: unauthorized document retrieval and citation leakage.

- Failure tests: empty documents, malformed documents, LLM errors,
  embedding failures, DB failures, timeouts.

- Frontend tests: chat states, citations, loading/errors,
  permission-sensitive UI.

- Do not rely only on end-to-end tests.

# 18. Docker / Local Development

- One command should start the local development dependencies.

- PostgreSQL must include pgvector.

- API and web apps should run independently for fast development.

- Provide health/readiness endpoints.

- Provide database migrations.

- Provide seed scripts for users, permissions and sample documents.

- Provide a reproducible evaluation command.

# 19. Environment Variables

- OPENAI_API_KEY

- OPENAI_MODEL

- EMBEDDING_MODEL

- DATABASE_URL

- APP_ENV

- LOG_LEVEL

- CORS_ORIGINS

- AUTH_SECRET / authentication configuration

- Optional tracing/observability configuration

Do not hard-code model names in business logic. Put provider/model
configuration behind configuration and service interfaces.

# 20. Frontend Requirements

- Chat interface.

- Streaming-ready response architecture, even if initial implementation
  returns a complete response.

- Citation/source panel.

- Loading/error/retry states.

- Document upload/admin view for development.

- Evaluation results view later.

- Basic request/trace ID visibility for developer debugging.

- Do not expose sensitive retrieval diagnostics to ordinary users.

# 21. Acceptance Criteria / Definition of Done

### Phase 1

A user can ask questions over seeded documents and receive grounded
answers.

### Phase 2

A new document can be ingested end-to-end without manually inserting
embeddings.

### Phase 3

Unauthorized users cannot retrieve or cite protected documents.

### Phase 4

Hybrid retrieval and reranking improve measurable retrieval quality on
the evaluation set.

### Phase 5

Document updates replace/deactivate stale content and citations remain
correct.

### Phase 6

A repeatable evaluation command reports retrieval and generation
metrics.

### Phase 7

A developer can trace a request, identify latency/token/cost breakdowns,
and diagnose retrieval failures.

# 22. How Claude Should Work With This Specification

16. First inspect the repository and this specification.

17. Do not start coding until you provide a proposed architecture and
    identify ambiguities.

18. Prefer the simplest architecture satisfying the current phase.

19. Do not implement future agent/MCP/workflow features early.

20. Implement one phase at a time.

21. After each phase: run tests, show changed files, explain important
    decisions and verify acceptance criteria.

22. Prefer explicit code over framework magic so the developer can learn
    the underlying RAG concepts.

23. When choosing a library, explain why it is needed and avoid
    unnecessary dependencies.

24. Use official/current documentation when package APIs or model APIs
    may have changed.

25. If a requirement conflicts with this document, stop and ask before
    making a major architectural change.

26. Keep a short Architecture Decision Record for meaningful decisions.

27. Never silently replace PostgreSQL/pgvector, FastAPI, Next.js, or the
    provider abstraction with another stack.

# 23. Future Extension Plan — Do Not Implement Yet

| Future capability                  | Planned evolution                                                                                       |
|------------------------------------|---------------------------------------------------------------------------------------------------------|
| Incremental/event-driven ingestion | Webhooks → queue → workers → retries → DLQ → reconciliation.                                            |
| Redis                              | Caching, rate limiting, short-lived state.                                                              |
| Agents                             | LLM-driven tool selection, state, loops, retries, guardrails.                                           |
| Tool calling                       | CRM, ticketing, ERP and knowledge tools with server-side authorization.                                 |
| MCP                                | Expose reusable enterprise tools/resources through MCP; use official MCP SDK v2 when this phase begins. |
| AI security                        | Prompt injection, indirect injection, tool permissions, audit controls.                                 |
| Workflow automation                | Deterministic business workflows, approvals, exception handling.                                        |
| Cloud                              | Docker production deployment, AWS services, CI/CD, secrets, observability.                              |
| FDE system design                  | Customer discovery, architecture trade-offs, scale, reliability, cost and business outcomes.            |

# 24. Future Change Requests

When a new learning topic is completed, append a change request here
rather than redesigning the entire project. Each change request should
state: new capability, business problem, affected components, new
requirements, security considerations, tests, acceptance criteria, and
whether it is a breaking change.

Template:

Change Request:  
Title:  
Why:  
New capability:  
Affected components:  
New APIs/data model:  
Security considerations:  
Tests:  
Acceptance criteria:  
Future dependencies:

# 25. Suggested Build Order

1\. Repository/bootstrap + Docker + PostgreSQL/pgvector + migrations.

2\. FastAPI health/readiness + configuration + database layer.

3\. Document model + seed documents + basic ingestion.

4\. Chunking + metadata + embeddings.

5\. Basic vector retrieval.

6\. LLM answer generation with grounded context.

7\. Next.js chat UI + citations.

8\. Authentication/authorization + permission-aware retrieval.

9\. Hybrid retrieval + reranking.

10\. Document versioning/freshness.

11\. Golden evaluation dataset + evaluation runner.

12\. Request tracing + latency/token/cost observability.

13\. Full test pass + architecture review + RAG interview review.

# 26. Final Outcome

At the end of RAG v1, the developer should be able to explain and
demonstrate: document ingestion, chunking, embeddings, pgvector, hybrid
retrieval, reranking, permission-aware retrieval, citations, document
freshness/versioning, evaluation, observability, latency/cost analysis,
API design, security boundaries, testing, Docker-based local
development, and the architectural extension points needed for future
Agents, Tool Calling, MCP, workflow automation and enterprise
integrations.

Current technology verification notes: Python 3.14.7 is the current
Python 3.14 maintenance release; OpenAI's current API supports Responses
API tools including function calling and remote MCP; the official MCP
TypeScript SDK v2 is the current stable 2026 SDK line. Exact
model/package versions should be pinned during implementation from the
official documentation.
