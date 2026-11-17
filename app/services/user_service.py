from fastapi import HTTPException
from sqlalchemy import func, select

from app.models import Review, User
from app.services import movie_service
from app.services.common import commit_or_409


def get_user(db, user_id):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def update_user(db, user_id, data):
    user = get_user(db, user_id)
    changes = {k: v for k, v in data.model_dump(exclude_unset=True).items() if v is not None}
    if "username" in changes:
        taken = db.scalar(
            select(User.id).where(func.lower(User.username) == changes["username"].lower(), User.id != user_id)
        )
        if taken is not None:
            raise HTTPException(status_code=409, detail="Username already taken")
    if "email" in changes:
        changes["email"] = str(changes["email"])
        taken = db.scalar(
            select(User.id).where(func.lower(User.email) == changes["email"].lower(), User.id != user_id)
        )
        if taken is not None:
            raise HTTPException(status_code=409, detail="Email already registered")
    for field, value in changes.items():
        setattr(user, field, value)
    commit_or_409(db, "Username or email already in use")
    return user


def delete_user(db, user_id):
    user = get_user(db, user_id)
    affected_movies = db.scalars(select(Review.movie_id).where(Review.user_id == user_id).distinct()).all()
    # reviews, watchlist items and tokens are removed by ON DELETE CASCADE
    db.delete(user)
    db.flush()
    for movie_id in affected_movies:
        movie_service.recalculate_rating(db, movie_id)
    db.commit()
