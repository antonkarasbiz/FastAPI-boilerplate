# FastAPI service boilerplate

Async API foundation for production backends: FastAPI, Pydantic v2, SQLAlchemy 2.0, PostgreSQL, and Redis. The tree is organized as vertical-slice modules with swappable infrastructure and a developer CLI.

## Overview

Use this repository when a new product needs auth, CRUD, background jobs, caching, and rate limits without assembling those pieces from scratch. It is the Python service template in the [antonkarasbiz](https://github.com/antonkarasbiz) full-stack and AI stack.

## Capabilities

- Fully async FastAPI + SQLAlchemy 2.0
- Pydantic v2 models and validation
- Server-side sessions, CSRF, OAuth, and API keys
- FastCRUD generics and pagination
- Optional SQLAdmin panel (environment toggle)
- Taskiq workers on Redis or RabbitMQ
- Redis or Memcached cache (`@cache` + provider API)
- Per-tier and per-path rate limits
- Alembic migrations with a production confirm gate
- `bp` CLI for compose files, env audit, and plugins
- Docker Compose for local, prod, and nginx-fronted shapes

## Repository layout

```text
FastAPI-boilerplate/
├── pyproject.toml          uv workspace root
├── backend/                deployable application
│   ├── src/                interfaces, infrastructure, modules
│   ├── pyproject.toml
│   └── Dockerfile
└── cli/                    bp — operator tool, not shipped in prod
```

## Quickstart

```bash
git clone https://github.com/antonkarasbiz/FastAPI-boilerplate
cd FastAPI-boilerplate
uv sync --all-packages --all-extras
```

Generate a compose file:

```bash
uv run bp deploy generate local
# uv run bp deploy generate prod
# uv run bp deploy generate nginx
```

Environment:

```bash
cp backend/.env.example backend/.env
uv run bp env gen-secret
uv run bp env validate
```

Start:

```bash
docker compose up --build
# http://127.0.0.1:8000  — OpenAPI at /docs
```

Without Docker (local Postgres + Redis required):

```bash
cd backend
uv run alembic upgrade head
uv run python -m scripts.setup_initial_data
```

## When to use it

Choose this template for a single deployable API that will grow by modules. It is not a microservices monorepo scaffold. Deeper operator notes live under `docs/`.

## License

MIT. Implementation follows the FastAPI-boilerplate / Fastro lineage. Upstream license terms apply.

## Maintainer

[Anton Karas](https://github.com/antonkarasbiz) — full-stack, blockchain, and AI engineering.
