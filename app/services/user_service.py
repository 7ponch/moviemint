from fastapi import HTTPException
from app import storage
from app.services import movie_service


def get_user(user_id):
    user = storage.users.get(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def update_user(user_id, data):
    user = get_user(user_id)
    changes = {k: v for k, v in data.model_dump(exclude_unset=True).items() if v is not None}
    for other in storage.users.values():
        if other["id"] == user_id:
            continue
        if "username" in changes and other["username"].lower() == changes["username"].lower():
            raise HTTPException(status_code=409, detail="Username already taken")
        if "email" in changes and other["email"].lower() == str(changes["email"]).lower():
            raise HTTPException(status_code=409, detail="Email already registered")
    if "email" in changes:
        changes["email"] = str(changes["email"])
    user.update(changes)
    return user


def delete_user(user_id):
    get_user(user_id)
    affected_movies = set()
    for review_id in [r["id"] for r in storage.reviews.values() if r["user_id"] == user_id]:
        affected_movies.add(storage.reviews[review_id]["movie_id"])
        del storage.reviews[review_id]
    for item_id in [i["id"] for i in storage.watchlist.values() if i["user_id"] == user_id]:
        del storage.watchlist[item_id]
    for token in [t for t, uid in storage.tokens.items() if uid == user_id]:
        del storage.tokens[token]
    del storage.users[user_id]
    for movie_id in affected_movies:
        if movie_id in storage.movies:
            movie_service.recalculate_rating(movie_id)