from fastapi import HTTPException
from sqlalchemy import select

from app.models import Review, WatchlistItem
from app.services import movie_service
from app.services.common import commit_or_409


def _find_item(db, user_id, movie_id):
    return db.scalar(
        select(WatchlistItem).where(WatchlistItem.user_id == user_id, WatchlistItem.movie_id == movie_id)
    )


def _get_item(db, user_id, movie_id):
    item = _find_item(db, user_id, movie_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Movie is not in your watchlist")
    return item


def _has_review(db, user_id, movie_id):
    stmt = select(Review.id).where(Review.user_id == user_id, Review.movie_id == movie_id)
    return db.scalar(stmt) is not None


def is_watched(db, user_id, movie_id):
    item = _find_item(db, user_id, movie_id)
    return item is not None and item.status == "watched"


def add_item(db, user_id, data):
    movie_service.get_movie(db, data.movie_id)
    if _find_item(db, user_id, data.movie_id) is not None:
        raise HTTPException(status_code=409, detail="Movie is already in your watchlist")
    item = WatchlistItem(user_id=user_id, movie_id=data.movie_id, status=data.status)
    db.add(item)
    commit_or_409(db, "Movie is already in your watchlist")
    return item


def list_items(db, user_id, status):
    stmt = select(WatchlistItem).where(WatchlistItem.user_id == user_id).order_by(WatchlistItem.id)
    if status:
        stmt = stmt.where(WatchlistItem.status == status)
    return db.scalars(stmt).all()


def update_status(db, user_id, movie_id, data):
    item = _get_item(db, user_id, movie_id)
    if data.status != "watched" and _has_review(db, user_id, movie_id):
        raise HTTPException(status_code=409, detail="Delete your review before changing the status back")
    item.status = data.status
    db.commit()
    return item


def remove_item(db, user_id, movie_id):
    item = _get_item(db, user_id, movie_id)
    if _has_review(db, user_id, movie_id):
        raise HTTPException(status_code=409, detail="Delete your review before removing the movie")
    db.delete(item)
    db.commit()
