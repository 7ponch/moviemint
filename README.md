# MovieMint

FastAPI backend with PostgreSQL (SQLAlchemy + Alembic) and JWT authentication.

## Run locally

```bash
# 1. PostgreSQL (or use your own server)
docker compose up -d

# 2. Python environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Configuration
cp .env.example .env            # edit DATABASE_URL, set a real SECRET_KEY

# 4. Create the tables from migrations
alembic upgrade head

# 5. Start the API
uvicorn app.main:app --reload

# 6. (optional) make an existing user an admin
python -m app.create_admin <username>            # --revoke to undo
```

Swagger UI: http://127.0.0.1:8000/docs

## Project structure

- `app/routers` - HTTP endpoints
- `app/schemas` - Pydantic request/response validation
- `app/services` - business logic
- `app/models` - SQLAlchemy tables
- `app/security.py` - bcrypt password hashing, JWT creation and validation
- `app/dependencies.py` - `get_current_user` and `require_admin` dependencies
- `app/database.py`, `app/config.py` - engine, sessions, settings from environment
- `tests` - pytest suite
- `alembic/versions` - migrations

## Authentication

1. `POST /auth/register` - `{username, email, password}`. Username and email are unique (case-insensitive); the password needs 8+ characters and a digit and is stored as a bcrypt hash.
2. `POST /auth/login` - `{username, password}` returns `{access_token, token_type: "bearer"}`. The token is a JWT (HS256) signed with `SECRET_KEY` and expires after `ACCESS_TOKEN_EXPIRE_MINUTES`.
3. Send `Authorization: Bearer <token>` on protected requests. In Swagger use the **Authorize** button.

Missing, malformed, expired or forged tokens return **401**. Authenticated users without permission get **403**.

## Authorization

Every user has a role: `user` (default) or `admin`. Roles cannot be set through the API; use `python -m app.create_admin`.

| Action | Anonymous | User | Admin |
|---|---|---|---|
| Browse movies and reviews | yes | yes | yes |
| Create / edit / delete movies | - | - | yes |
| Random movie, watchlist, write reviews | - | yes | yes |
| Edit a review | - | own only | own only |
| Delete a review | - | own only | any |
| Watchlist | - | own only | own only |
| Edit / delete account (`/me`) | - | self | self |

## Tests

```bash
pytest
```

Tests run against a separate PostgreSQL database (`<your db>_test`, or `TEST_DATABASE_URL`). It is created automatically, migrated with Alembic and wiped on every run.

## Migrations

```bash
alembic revision --autogenerate -m "describe change"
alembic upgrade head
alembic downgrade -1
```

## Data model

- `users` 1 - N `reviews`, `watchlist_items`; `users.role` is `user` or `admin`
- `movies` 1 - N `reviews`, `watchlist_items`
- `reviews` and `watchlist_items`: unique per (user, movie)
- Foreign keys use `ON DELETE CASCADE`
