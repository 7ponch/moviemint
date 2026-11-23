import pytest

from app import create_admin
from app.models import User

NEW_MOVIE = {"title": "Dune", "year": 2021, "genre": "Sci-Fi"}


class TestMovieAdminOnly:
    def test_admin_can_manage_movies(self, client, admin_headers):
        created = client.post("/movies", json=NEW_MOVIE, headers=admin_headers)
        assert created.status_code == 201
        movie_id = created.json()["id"]
        updated = client.patch(f"/movies/{movie_id}", json={"genre": "Drama"}, headers=admin_headers)
        assert updated.status_code == 200
        assert updated.json()["genre"] == "Drama"
        assert client.delete(f"/movies/{movie_id}", headers=admin_headers).status_code == 204

    def test_regular_user_cannot_create_movie(self, client, user_headers):
        response = client.post("/movies", json=NEW_MOVIE, headers=user_headers)
        assert response.status_code == 403
        assert response.json()["detail"] == "Admin access required"

    def test_regular_user_cannot_update_or_delete_movie(self, client, movie, user_headers):
        assert client.patch(f"/movies/{movie['id']}", json={"genre": "X"}, headers=user_headers).status_code == 403
        assert client.delete(f"/movies/{movie['id']}", headers=user_headers).status_code == 403
        assert client.get(f"/movies/{movie['id']}").json()["genre"] == "Sci-Fi"

    def test_anonymous_cannot_manage_movies(self, client, movie):
        assert client.post("/movies", json=NEW_MOVIE).status_code == 401
        assert client.patch(f"/movies/{movie['id']}", json={"genre": "X"}).status_code == 401
        assert client.delete(f"/movies/{movie['id']}").status_code == 401

    def test_demoted_admin_loses_access_with_old_token(self, client, admin_headers, session_factory):
        with session_factory() as db:
            db.query(User).filter_by(username="root").update({"role": "user"})
            db.commit()
        assert client.post("/movies", json=NEW_MOVIE, headers=admin_headers).status_code == 403


@pytest.fixture
def review(client, movie, user_headers):
    client.post("/me/watchlist", json={"movie_id": movie["id"], "status": "watched"}, headers=user_headers)
    response = client.post(f"/movies/{movie['id']}/reviews", json={"rating": 9, "text": "Great"}, headers=user_headers)
    assert response.status_code == 201
    return response.json()


class TestReviewOwnership:
    def test_owner_can_edit_and_delete(self, client, review, user_headers):
        assert client.patch(f"/reviews/{review['id']}", json={"rating": 7}, headers=user_headers).status_code == 200
        assert client.delete(f"/reviews/{review['id']}", headers=user_headers).status_code == 204

    def test_other_user_cannot_edit(self, client, review, other_headers):
        response = client.patch(f"/reviews/{review['id']}", json={"rating": 1}, headers=other_headers)
        assert response.status_code == 403

    def test_other_user_cannot_delete(self, client, review, movie, other_headers):
        assert client.delete(f"/reviews/{review['id']}", headers=other_headers).status_code == 403
        assert len(client.get(f"/movies/{movie['id']}/reviews").json()) == 1

    def test_admin_can_delete_any_review(self, client, review, movie, admin_headers):
        assert client.delete(f"/reviews/{review['id']}", headers=admin_headers).status_code == 204
        assert client.get(f"/movies/{movie['id']}/reviews").json() == []
        assert client.get(f"/movies/{movie['id']}").json()["reviews_count"] == 0

    def test_admin_cannot_edit_someone_elses_review(self, client, review, admin_headers):
        response = client.patch(f"/reviews/{review['id']}", json={"text": "edited"}, headers=admin_headers)
        assert response.status_code == 403


class TestWatchlistIsolation:
    def test_users_only_see_their_own_watchlist(self, client, movie, user_headers, other_headers):
        client.post("/me/watchlist", json={"movie_id": movie["id"]}, headers=user_headers)
        assert len(client.get("/me/watchlist", headers=user_headers).json()) == 1
        assert client.get("/me/watchlist", headers=other_headers).json() == []

    def test_users_cannot_modify_others_watchlist(self, client, movie, user_headers, other_headers):
        client.post("/me/watchlist", json={"movie_id": movie["id"]}, headers=user_headers)
        path = f"/me/watchlist/{movie['id']}"
        assert client.patch(path, json={"status": "watched"}, headers=other_headers).status_code == 404
        assert client.delete(path, headers=other_headers).status_code == 404
        items = client.get("/me/watchlist", headers=user_headers).json()
        assert items[0]["status"] == "planned"


class TestRoleEscalation:
    def test_user_cannot_promote_self(self, client, user_headers):
        response = client.patch("/me", json={"role": "admin"}, headers=user_headers)
        assert response.status_code == 200
        assert client.get("/auth/me", headers=user_headers).json()["role"] == "user"
        assert client.post("/movies", json=NEW_MOVIE, headers=user_headers).status_code == 403

    def test_create_admin_script(self, client, user_headers, session_factory, monkeypatch):
        monkeypatch.setattr(create_admin, "SessionLocal", session_factory)
        assert create_admin.set_role("ALICE", "admin") == 0
        assert client.post("/movies", json=NEW_MOVIE, headers=user_headers).status_code == 201
        assert create_admin.set_role("alice", "user") == 0
        assert client.get("/auth/me", headers=user_headers).json()["role"] == "user"

    def test_create_admin_script_unknown_user(self, session_factory, monkeypatch):
        monkeypatch.setattr(create_admin, "SessionLocal", session_factory)
        assert create_admin.set_role("ghost", "admin") == 1
