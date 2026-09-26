# Ignite RAG v1

A secure, permission-aware RAG assistant for a fictional enterprise (Ignite),
built as a learning project toward a Forward Deployed Engineer role —
FastAPI + Postgres/pgvector + Next.js, built one phase at a time.

[![CI](https://github.com/graj8899/ignite-ai/actions/workflows/ci.yml/badge.svg)](https://github.com/graj8899/ignite-ai/actions/workflows/ci.yml)

## Quickstart

```bash
# 1. Start Postgres + pgvector
cp .env.example .env   # then fill in real values
docker compose up -d

# 2. Install API dependencies and run migrations
cd apps/api
uv sync
uv run alembic upgrade head

# 3. Run the API
uv run fastapi dev app/main.py
# -> http://localhost:8000/docs

# 4. Lint and test
uv run ruff check .
uv run ruff format --check .
uv run pytest                    # unit tests (no DB needed)
uv run pytest -m integration     # integration tests (needs the DB running)
```

## Docs

- [CLAUDE.md](CLAUDE.md) — working rules and source-of-truth precedence for AI-assisted development on this repo
- [docs/spec/rag-v1-spec.md](docs/spec/rag-v1-spec.md) — original build specification
- [docs/decisions/](docs/decisions/) — Architecture Decision Records (ADRs)
- [docs/architecture/overview.md](docs/architecture/overview.md) — architecture, flows, repo layout
- [docs/learning/](docs/learning/) — phase-by-phase learning notes
