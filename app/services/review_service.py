from fastapi import HTTPException
from sqlalchemy import select

from app.models import Review
from app.services import movie_service, watchlist_service
from app.services.common import commit_or_409


def _get_review(db, review_id):
    review = db.get(Review, review_id)
    if review is None:
        raise HTTPException(status_code=404, detail="Review not found")
    return review


def create_review(db, movie_id, user_id, data):
    movie_service.get_movie(db, movie_id)
    if not watchlist_service.is_watched(db, user_id, movie_id):
        raise HTTPException(status_code=400, detail="Mark the movie as watched before reviewing it")
    existing = db.scalar(select(Review.id).where(Review.user_id == user_id, Review.movie_id == movie_id))
    if existing is not None:
        raise HTTPException(status_code=409, detail="You already reviewed this movie")
    review = Review(user_id=user_id, movie_id=movie_id, rating=data.rating, text=data.text)
    db.add(review)
    db.flush()
    movie_service.recalculate_rating(db, movie_id)
    commit_or_409(db, "You already reviewed this movie")
    return review


def list_reviews(db, movie_id):
    movie_service.get_movie(db, movie_id)
    return db.scalars(select(Review).where(Review.movie_id == movie_id).order_by(Review.id)).all()


def update_review(db, review_id, user_id, data):
    review = _get_review(db, review_id)
    if review.user_id != user_id:
        raise HTTPException(status_code=403, detail="You can only edit your own review")
    changes = {k: v for k, v in data.model_dump(exclude_unset=True).items() if v is not None}
    for field, value in changes.items():
        setattr(review, field, value)
    db.flush()
    movie_service.recalculate_rating(db, review.movie_id)
    db.commit()
    return review


def delete_review(db, review_id, user_id):
    review = _get_review(db, review_id)
    if review.user_id != user_id:
        raise HTTPException(status_code=403, detail="You can only delete your own review")
    movie_id = review.movie_id
    db.delete(review)
    db.flush()
    movie_service.recalculate_rating(db, movie_id)
    db.commit()
