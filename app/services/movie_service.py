from fastapi import HTTPException
from sqlalchemy import func, select

from app.models import Movie, Review, WatchlistItem
from app.services.common import commit_or_409

HIDDEN_GEM_MIN_RATING = 8.0
HIDDEN_GEM_MAX_REVIEWS = 5


def _title_taken(db, title, year, exclude_id=None):
    stmt = select(Movie.id).where(func.lower(Movie.title) == title.lower(), Movie.year == year)
    if exclude_id is not None:
        stmt = stmt.where(Movie.id != exclude_id)
    return db.scalar(stmt) is not None


def create_movie(db, data):
    if _title_taken(db, data.title, data.year):
        raise HTTPException(status_code=409, detail="Movie already exists")
    movie = Movie(**data.model_dump())
    db.add(movie)
    commit_or_409(db, "Movie already exists")
    return movie


def get_movie(db, movie_id):
    movie = db.get(Movie, movie_id)
    if movie is None:
        raise HTTPException(status_code=404, detail="Movie not found")
    return movie


def list_movies(db, genre, q, section):
    stmt = select(Movie).order_by(Movie.id)
    if genre:
        stmt = stmt.where(func.lower(Movie.genre) == genre.lower())
    if q:
        stmt = stmt.where(Movie.title.icontains(q, autoescape=True))
    if section:
        stmt = stmt.where(Movie.section == section)
    return db.scalars(stmt).all()


def update_movie(db, movie_id, data):
    movie = get_movie(db, movie_id)
    changes = {k: v for k, v in data.model_dump(exclude_unset=True).items() if v is not None}
    new_title = changes.get("title", movie.title)
    new_year = changes.get("year", movie.year)
    if _title_taken(db, new_title, new_year, exclude_id=movie_id):
        raise HTTPException(status_code=409, detail="Movie already exists")
    for field, value in changes.items():
        setattr(movie, field, value)
    commit_or_409(db, "Movie already exists")
    return movie


def delete_movie(db, movie_id):
    movie = get_movie(db, movie_id)
    # reviews and watchlist items are removed by ON DELETE CASCADE
    db.delete(movie)
    db.commit()


def get_random_movie(db, user_id, genre):
    watched = select(WatchlistItem.movie_id).where(
        WatchlistItem.user_id == user_id, WatchlistItem.status == "watched"
    )
    stmt = select(Movie).where(Movie.id.not_in(watched))
    if genre:
        stmt = stmt.where(func.lower(Movie.genre) == genre.lower())
    movie = db.scalar(stmt.order_by(func.random()).limit(1))
    if movie is None:
        raise HTTPException(status_code=404, detail="No unwatched movies found")
    return movie


def recalculate_rating(db, movie_id):
    """Updates rating, reviews_count and section. The caller commits."""
    average, count = db.execute(
        select(func.avg(Review.rating), func.count(Review.id)).where(Review.movie_id == movie_id)
    ).one()
    movie = db.get(Movie, movie_id)
    movie.reviews_count = count
    if count == 0:
        movie.rating = 0.0
        return
    average = float(average)
    movie.rating = round(average, 1)
    is_gem = average >= HIDDEN_GEM_MIN_RATING and count < HIDDEN_GEM_MAX_REVIEWS
    movie.section = "hidden_gem" if is_gem else "mainstream"
