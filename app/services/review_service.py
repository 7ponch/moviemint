from fastapi import HTTPException
from app import storage
from app.services import movie_service, watchlist_service


def _get_review(review_id):
    review = storage.reviews.get(review_id)
    if review is None:
        raise HTTPException(status_code=404, detail="Review not found")
    return review


def create_review(movie_id, user_id, data):
    movie_service.get_movie(movie_id)
    if not watchlist_service.is_watched(user_id, movie_id):
        raise HTTPException(status_code=400, detail="Mark the movie as watched before reviewing it")
    for review in storage.reviews.values():
        if review["user_id"] == user_id and review["movie_id"] == movie_id:
            raise HTTPException(status_code=409, detail="You already reviewed this movie")
    review_id = storage.next_id("review")
    review = {
        "id": review_id,
        "user_id": user_id,
        "movie_id": movie_id,
        "rating": data.rating,
        "text": data.text,
    }
    storage.reviews[review_id] = review
    movie_service.recalculate_rating(movie_id)
    return review


def list_reviews(movie_id):
    movie_service.get_movie(movie_id)
    return [r for r in storage.reviews.values() if r["movie_id"] == movie_id]


def update_review(review_id, user_id, data):
    review = _get_review(review_id)
    if review["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="You can only edit your own review")
    changes = {k: v for k, v in data.model_dump(exclude_unset=True).items() if v is not None}
    review.update(changes)
    movie_service.recalculate_rating(review["movie_id"])
    return review


def delete_review(review_id, user_id):
    review = _get_review(review_id)
    if review["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="You can only delete your own review")
    movie_id = review["movie_id"]
    del storage.reviews[review_id]
    movie_service.recalculate_rating(movie_id)