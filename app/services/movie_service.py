import random

from fastapi import HTTPException
from app import storage

HIDDEN_GEM_MIN_RATING = 8.0
HIDDEN_GEM_MAX_REVIEWS = 5


def _title_taken(title, year, exclude_id=None):
    for movie in storage.movies.values():
        if movie["id"] != exclude_id and movie["title"].lower() == title.lower() and movie["year"] == year:
            return True
    return False


def create_movie(data):
    if _title_taken(data.title, data.year):
        raise HTTPException(status_code=409, detail="Movie already exists")
    movie_id = storage.next_id("movie")
    movie = {"id": movie_id, **data.model_dump(), "rating": 0.0, "reviews_count": 0}
    storage.movies[movie_id] = movie
    return movie


def get_movie(movie_id):
    movie = storage.movies.get(movie_id)
    if movie is None:
        raise HTTPException(status_code=404, detail="Movie not found")
    return movie


def list_movies(genre, q, section):
    result = list(storage.movies.values())
    if genre:
        result = [m for m in result if m["genre"].lower() == genre.lower()]
    if q:
        result = [m for m in result if q.lower() in m["title"].lower()]
    if section:
        result = [m for m in result if m["section"] == section]
    return result


def update_movie(movie_id, data):
    movie = get_movie(movie_id)
    changes = {k: v for k, v in data.model_dump(exclude_unset=True).items() if v is not None}
    new_title = changes.get("title", movie["title"])
    new_year = changes.get("year", movie["year"])
    if _title_taken(new_title, new_year, exclude_id=movie_id):
        raise HTTPException(status_code=409, detail="Movie already exists")
    movie.update(changes)
    return movie


def delete_movie(movie_id):
    get_movie(movie_id)
    for review_id in [r["id"] for r in storage.reviews.values() if r["movie_id"] == movie_id]:
        del storage.reviews[review_id]
    for item_id in [i["id"] for i in storage.watchlist.values() if i["movie_id"] == movie_id]:
        del storage.watchlist[item_id]
    del storage.movies[movie_id]


def get_random_movie(user_id, genre):
    watched = {
        i["movie_id"]
        for i in storage.watchlist.values()
        if i["user_id"] == user_id and i["status"] == "watched"
    }
    candidates = [m for m in storage.movies.values() if m["id"] not in watched]
    if genre:
        candidates = [m for m in candidates if m["genre"].lower() == genre.lower()]
    if not candidates:
        raise HTTPException(status_code=404, detail="No unwatched movies found")
    return random.choice(candidates)


def recalculate_rating(movie_id):
    movie = storage.movies[movie_id]
    ratings = [r["rating"] for r in storage.reviews.values() if r["movie_id"] == movie_id]
    count = len(ratings)
    movie["reviews_count"] = count
    if count == 0:
        movie["rating"] = 0.0
        return
    average = sum(ratings) / count
    movie["rating"] = round(average, 1)
    is_gem = average >= HIDDEN_GEM_MIN_RATING and count < HIDDEN_GEM_MAX_REVIEWS
    movie["section"] = "hidden_gem" if is_gem else "mainstream"