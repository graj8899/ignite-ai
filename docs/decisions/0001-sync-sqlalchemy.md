# ADR-0001: Sync SQLAlchemy (not async) for v1

Status: Accepted (2026-09-26)

## Context

SQLAlchemy 2.x supports both a synchronous API and an async one (paired with
an async driver, e.g. `psycopg` in async mode or `asyncpg`). Async avoids
blocking a worker thread on I/O, which matters once concurrent DB-bound
requests exceed what a thread pool can absorb.

## Decision

Use **sync** SQLAlchemy + `psycopg[binary]` (v3, sync mode) for RAG v1.

FastAPI runs sync path-operation functions and sync dependencies in a
background thread pool automatically, so we still get real request
concurrency — just bounded by the thread pool size (default 40 threads)
rather than the event loop.

## Why this is enough at our load

The spec's scale assumptions are ~8,000 questions/day. That is roughly
0.1 requests/second on average; even at a peaky 10x burst factor it's under
1 req/s sustained. Each request's actual DB time (a few indexed queries) is
milliseconds. Sync SQLAlchemy with a small connection pool comfortably
serves this without threads or connections becoming the bottleneck — the
bottleneck at this scale is the LLM call, not the database.

Sync code is also simpler to read, debug and teach: no `await` threading
through every function, no separate async test fixtures, one mental model
end-to-end. That fits the project's teach-as-we-go, explicit-over-magic
goals.

## When we would switch to async

Concrete signals to revisit this decision:

- Thread-pool exhaustion: request latency climbing under load while CPU and
  DB are idle (a sign requests are queued waiting for a free worker thread).
- Sustained concurrent request volume that materially exceeds ~40 in-flight
  DB-bound requests (i.e. real enterprise-scale traffic, not v1's assumed
  load).
- A move to an async-native deployment model (e.g. many short-lived
  serverless invocations) where thread pools are a poor fit.

If that happens, the migration path is: swap `psycopg` sync engine for its
async mode (or `asyncpg`), change `Session` to `AsyncSession`, and make
route/dependency functions `async def`. Keeping DB access behind
`app/db.py` and `app/repositories/` (per the architecture doc) means this
change stays localized rather than rippling through the whole codebase.

## Consequences

- `app/db.py` exposes a sync `Session` via a FastAPI dependency.
- Repositories (`app/repositories/`) are written with sync SQLAlchemy calls.
- Alembic runs sync (its default mode); no async migration tooling needed.
