# Contributing

Thanks for helping build this bot. The project is intentionally modular: each
feature should live under `app/modules/<name>/` with a Discord cog, FastAPI
routes, SQLAlchemy models, Pydantic schemas, shared service logic, and optional
frontend code.

## Local Dev Loop

1. Install Python 3.12, Node 20+, Docker, and `uv`.
2. Copy `.env.example` to `.env` and fill in Discord credentials.
3. Install Python dependencies:

   ```bash
   uv sync
   ```

4. Install frontend dependencies:

   ```bash
   cd frontend
   npm install
   ```

5. Run the stack:

   ```bash
   docker compose up --build
   ```

6. Run checks before opening a PR:

   ```bash
   uv run ruff format .
   uv run ruff check .
   uv run pytest
   cd frontend && npm run build
   ```

## Module Rules

- Keep business logic in `service.py`.
- Keep Discord-specific interaction code in `cog.py`, `discord_views.py`, and
  `discord_modals.py`.
- Keep FastAPI request/response concerns in `routes.py`.
- Add SQLAlchemy models in `models.py` and Pydantic contracts in `schemas.py`.
- Add an Alembic migration for every schema change.
- Persistent Discord views must use stable `custom_id` values and be registered
  on bot startup.
