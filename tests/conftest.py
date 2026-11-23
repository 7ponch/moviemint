import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.database import get_db
from app.main import app
from app.models import User


def _test_database_url():
    if settings.test_database_url:
        url = make_url(settings.test_database_url)
    else:
        main = make_url(settings.database_url)
        url = main.set(database=f"{main.database}_test")
    if not url.database.endswith("_test"):
        raise RuntimeError("Refusing to run tests against a database whose name does not end with '_test'")
    return url


def _ensure_database(url):
    admin_engine = create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin_engine.connect() as conn:
        exists = conn.scalar(text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": url.database})
        if not exists:
            conn.execute(text(f'CREATE DATABASE "{url.database}"'))
    admin_engine.dispose()


@pytest.fixture(scope="session")
def engine():
    url = _test_database_url()
    _ensure_database(url)
    engine = create_engine(url)
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
    config = Config("alembic.ini")
    config.attributes["database_url"] = url.render_as_string(hide_password=False)
    command.upgrade(config, "head")
    yield engine
    engine.dispose()


@pytest.fixture
def session_factory(engine):
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    yield factory
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE users, movies RESTART IDENTITY CASCADE"))


@pytest.fixture
def client(session_factory):
    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def register(client, username, password="secret123", email=None):
    return client.post(
        "/auth/register",
        json={"username": username, "email": email or f"{username}@example.com", "password": password},
    )


def login(client, username, password="secret123"):
    return client.post("/auth/login", json={"username": username, "password": password})


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def make_user(client, session_factory):
    def _make(username, role="user"):
        assert register(client, username).status_code == 201
        if role != "user":
            with session_factory() as db:
                db.query(User).filter(User.username == username).update({"role": role})
                db.commit()
        token = login(client, username).json()["access_token"]
        return auth_headers(token)

    return _make


@pytest.fixture
def user_headers(make_user):
    return make_user("alice")


@pytest.fixture
def other_headers(make_user):
    return make_user("bob")


@pytest.fixture
def admin_headers(make_user):
    return make_user("root", role="admin")


@pytest.fixture
def movie(client, admin_headers):
    response = client.post(
        "/movies",
        json={"title": "Arrival", "year": 2016, "genre": "Sci-Fi"},
        headers=admin_headers,
    )
    assert response.status_code == 201
    return response.json()
