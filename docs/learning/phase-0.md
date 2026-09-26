# Phase 0 — Foundations

What we built, in five steps, before writing any RAG logic: a documented
repo, a local database, a runnable API skeleton, a real database layer with
migrations, and CI that checks all of it automatically.

## What we built

**0.1 — Project docs.** `CLAUDE.md` (working rules and source-of-truth
precedence), `.gitignore`, and the initial git repo/commit.

**0.2 — Local Postgres.** `docker-compose.yml` running
`pgvector/pgvector:0.8.6-pg17` (pinned, not `latest`), a named volume so data
survives restarts, a healthcheck, and `.env.example` documenting every
required environment variable.

**0.3 — FastAPI skeleton.** A `uv`-managed Python project, a `create_app()`
factory, `Settings` (typed config from env/`.env`, no defaults for secrets),
`GET /api/health`, and request-ID middleware (every request gets a
request ID, generated or passed through, for tracing).

**0.4 — Database layer.** SQLAlchemy (sync) + `psycopg` v3, a lazily-created
engine/session (importing the app never touches the database), Alembic
migrations reading the DB URL from `Settings` (never hard-coded), a first
migration enabling the `vector` extension, and `GET /api/readiness` (checks
the DB is reachable and pgvector is installed).

**0.5 — CI.** GitHub Actions running lint, unit tests, and (against a real
throwaway Postgres) migrations + integration tests on every push/PR.

## Key concepts, in plain language

- **Modular monolith**: one deployable backend, but code is organized into
  clearly separated modules (auth, retrieval, rag, ...) that only talk to
  each other through plain function calls. You get the simplicity of one
  app and the option to split a module into its own service later.

- **Settings from environment variables**: instead of hard-coding config
  (API keys, model names, DB connection strings) into code, the app reads
  them from environment variables at startup. This means the same code runs
  in dev/test/prod just by changing environment — and secrets never end up
  in git history.

- **Dependency injection (FastAPI's `Depends`)**: a route declares what it
  needs (like a database session) as a parameter, and the framework
  supplies it. This makes testing easy: a test can swap in a fake dependency
  without changing the route's code at all.

- **Lazy initialization**: the database engine is built only the first time
  it's actually needed, not the moment the module is imported. This keeps
  `import app.main` side-effect-free — you can inspect or test the app's
  code without a database being available at all.

- **Migrations (Alembic)**: instead of hand-editing the database schema, every
  change is a versioned, ordered script with an `upgrade()` and a
  `downgrade()`. This gives a repeatable, reviewable history of every schema
  change, and a way to undo one if it goes wrong.

- **Health vs. readiness**: `/api/health` answers "is the process running?"
  `/api/readiness` answers "can it actually do its job right now?" (reach
  the database, have the extensions it needs). Orchestrators use readiness
  to decide whether to send traffic to an instance.

- **CI service containers**: a GitHub Actions job can start a temporary,
  disposable Postgres container just for that run, so integration tests
  exercise a real database without any shared, persistent infrastructure.

## Likely interview questions

**Q: Why a modular monolith instead of microservices from day one?**
A: At this scale (thousands of requests/day, one small team), microservices
add network calls, deployment complexity, and distributed-systems failure
modes for no real benefit. A modular monolith gets the same code
organization and future flexibility to extract a service later, without
paying that cost now.

**Q: Why sync SQLAlchemy instead of async?**
A: Async matters when I/O concurrency is the bottleneck at high request
volume. At ~8,000 requests/day, sync SQLAlchemy (with FastAPI running sync
code in a thread pool) is simple, easy to debug, and nowhere near its
limits — the real bottleneck at this scale is LLM latency, not the DB. See
[ADR-0001](../decisions/0001-sync-sqlalchemy.md) for the concrete signals
that would justify switching.

**Q: Why does the database engine get created lazily instead of at import
time?**
A: Importing a module shouldn't have side effects like opening a network
connection or requiring secrets to exist — it makes the code impossible to
inspect, test, or even import in environments without a database (like a CI
lint step). Building the engine on first *use* keeps imports cheap and safe.

**Q: What does `pool_pre_ping=True` do, and why do you need it?**
A: Before handing out a pooled connection, SQLAlchemy sends a lightweight
"are you alive?" check and transparently reconnects if not. Without it,
you'd occasionally get a "connection already closed" error from a
connection that went stale (e.g., after the DB restarted) even though your
code did nothing wrong.

**Q: Why store request IDs, and why validate the incoming header instead
of trusting it?**
A: A request ID lets you trace one request's logs across every layer of the
system — essential for debugging in production. Trusting an arbitrary
client-supplied header value would let a malicious caller inject control
characters into logs or downstream headers, so it's validated against a
strict allowlist before being reused.

**Q: What's the difference between `/api/health` and `/api/readiness`?**
A: Health says "the process is alive"; readiness says "the process can
serve real traffic" — e.g., the database is reachable and has what the app
needs (like the pgvector extension). A load balancer uses readiness to
decide whether to route requests to an instance, and health to decide
whether to restart it.

**Q: Why does the readiness endpoint return a generic message on failure
instead of the real error?**
A: Leaking internal error details (stack traces, connection strings,
internal hostnames) to an API caller is an information-disclosure risk. The
real error is logged server-side, tagged with the request ID, so a
developer can look it up — but the client only sees "not ready."

**Q: Why did you prove the Alembic `downgrade()` actually works, instead
of just writing it?**
A: A `downgrade()` function that's written but never executed can silently
be broken (wrong SQL, wrong order) and you wouldn't find out until you
actually needed to roll back in production — the worst possible time to
discover it. Running `downgrade` then `upgrade` again in CI proves the
round-trip works on every change.

**Q: Why pin the pgvector Docker image to an exact tag instead of using
`latest`?**
A: `latest` can silently change what you're running between one `docker
compose up` and the next, breaking reproducibility — "works on my machine"
today might not tomorrow. Pinning (`0.8.6-pg17`) means every developer and
CI run gets the identical, tested image.

**Q: Why does CI use fake environment variable values instead of real
secrets for the integration job?**
A: The integration tests only need the app to *start* and reach a real,
disposable database — they don't call OpenAI. Using obviously-fake values
(`ci-dummy-key`) avoids ever needing a real secret in CI for this job,
which reduces what could leak if the CI environment were compromised.
