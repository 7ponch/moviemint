# MovieMint

FastAPI backend with PostgreSQL (SQLAlchemy + Alembic).

## Run locally

```bash
# 1. PostgreSQL (or use your own server)
docker compose up -d

# 2. Python environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Configuration
cp .env.example .env            # edit DATABASE_URL if needed

# 4. Create the tables from migrations
alembic upgrade head

# 5. Start the API
uvicorn app.main:app --reload
```

Swagger UI: http://127.0.0.1:8000/docs

## Project structure

- `app/routers` - HTTP endpoints
- `app/schemas` - Pydantic request/response validation
- `app/services` - business logic
- `app/models` - SQLAlchemy tables
- `app/database.py`, `app/config.py` - engine, sessions, settings from environment
- `alembic/versions` - migrations

## Migrations

```bash
alembic revision --autogenerate -m "describe change"
alembic upgrade head
alembic downgrade -1
```

## Data model

- `users` 1 - N `reviews`, `watchlist_items`, `auth_tokens`
- `movies` 1 - N `reviews`, `watchlist_items`
- `reviews` and `watchlist_items`: unique per (user, movie)
- Foreign keys use `ON DELETE CASCADE`
