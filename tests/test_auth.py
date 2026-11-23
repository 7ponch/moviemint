from datetime import datetime, timedelta, timezone

import jwt
import pytest

from app.config import settings
from app.models import User
from tests.conftest import auth_headers, login, register


class TestRegistration:
    def test_register_success(self, client):
        response = register(client, "alice")
        assert response.status_code == 201
        body = response.json()
        assert body["username"] == "alice"
        assert body["email"] == "alice@example.com"
        assert body["role"] == "user"
        assert "password" not in body and "password_hash" not in body

    def test_password_is_stored_as_bcrypt_hash(self, client, session_factory):
        register(client, "alice", password="secret123")
        with session_factory() as db:
            user = db.query(User).filter_by(username="alice").one()
        assert user.password_hash != "secret123"
        assert user.password_hash.startswith("$2b$")

    def test_duplicate_username_rejected(self, client):
        register(client, "alice")
        response = register(client, "ALICE", email="other@example.com")
        assert response.status_code == 409
        assert response.json()["detail"] == "Username already taken"

    def test_duplicate_email_rejected(self, client):
        register(client, "alice")
        response = register(client, "alice2", email="Alice@Example.com")
        assert response.status_code == 409
        assert response.json()["detail"] == "Email already registered"

    @pytest.mark.parametrize(
        "payload",
        [
            {"username": "al", "email": "a@example.com", "password": "secret123"},
            {"username": "bad name!", "email": "a@example.com", "password": "secret123"},
            {"username": "alice", "email": "not-an-email", "password": "secret123"},
            {"username": "alice", "email": "a@example.com", "password": "short1"},
            {"username": "alice", "email": "a@example.com", "password": "nodigitshere"},
            {"username": "alice", "email": "a@example.com"},
        ],
    )
    def test_invalid_registration_data(self, client, payload):
        assert client.post("/auth/register", json=payload).status_code == 422

    def test_role_cannot_be_set_on_registration(self, client):
        response = client.post(
            "/auth/register",
            json={"username": "sneaky", "email": "s@example.com", "password": "secret123", "role": "admin"},
        )
        assert response.status_code == 201
        assert response.json()["role"] == "user"


class TestLogin:
    def test_login_returns_jwt(self, client):
        register(client, "alice")
        response = login(client, "alice")
        assert response.status_code == 200
        body = response.json()
        assert body["token_type"] == "bearer"
        payload = jwt.decode(body["access_token"], settings.secret_key, algorithms=[settings.jwt_algorithm])
        assert payload["sub"] == "1"
        assert payload["role"] == "user"
        assert payload["exp"] > payload["iat"]

    def test_login_is_case_insensitive_for_username(self, client):
        register(client, "alice")
        assert login(client, "ALICE").status_code == 200

    def test_wrong_password(self, client):
        register(client, "alice")
        response = login(client, "alice", password="wrong1234")
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid username or password"

    def test_unknown_user(self, client):
        response = login(client, "ghost")
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid username or password"

    def test_missing_fields(self, client):
        assert client.post("/auth/login", json={"username": "alice"}).status_code == 422


def _token(sub, *, minutes=5, key=None, algorithm="HS256"):
    now = datetime.now(timezone.utc)
    payload = {"sub": sub, "iat": now, "exp": now + timedelta(minutes=minutes)}
    return jwt.encode(payload, key or settings.secret_key, algorithm=algorithm)


class TestProtectedEndpoint:
    def test_me_with_valid_token(self, client, user_headers):
        response = client.get("/auth/me", headers=user_headers)
        assert response.status_code == 200
        assert response.json()["username"] == "alice"

    def test_me_without_token(self, client):
        response = client.get("/auth/me")
        assert response.status_code == 401
        assert response.headers["www-authenticate"] == "Bearer"

    def test_me_with_garbage_token(self, client):
        response = client.get("/auth/me", headers=auth_headers("not.a.jwt"))
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid token"

    def test_me_with_wrong_scheme(self, client):
        assert client.get("/auth/me", headers={"Authorization": "Basic abc"}).status_code == 401

    def test_me_with_expired_token(self, client, user_headers):
        response = client.get("/auth/me", headers=auth_headers(_token("1", minutes=-1)))
        assert response.status_code == 401
        assert response.json()["detail"] == "Token expired"

    def test_me_with_token_signed_by_other_key(self, client, user_headers):
        response = client.get("/auth/me", headers=auth_headers(_token("1", key="x" * 48)))
        assert response.status_code == 401

    def test_me_with_unsigned_token(self, client, user_headers):
        token = jwt.encode({"sub": "1", "exp": 9999999999}, None, algorithm="none")
        assert client.get("/auth/me", headers=auth_headers(token)).status_code == 401

    def test_token_of_deleted_user(self, client, user_headers):
        assert client.delete("/me", headers=user_headers).status_code == 204
        assert client.get("/auth/me", headers=user_headers).status_code == 401

    def test_protected_routes_require_token(self, client, movie):
        assert client.get("/me/watchlist").status_code == 401
        assert client.post("/me/watchlist", json={"movie_id": movie["id"]}).status_code == 401
        assert client.get("/movies/random").status_code == 401
        assert client.patch("/me", json={"username": "x_x"}).status_code == 401
        assert client.post(f"/movies/{movie['id']}/reviews", json={"rating": 5}).status_code == 401

    def test_public_routes_work_without_token(self, client, movie):
        assert client.get("/movies").status_code == 200
        assert client.get(f"/movies/{movie['id']}").status_code == 200
        assert client.get(f"/movies/{movie['id']}/reviews").status_code == 200
