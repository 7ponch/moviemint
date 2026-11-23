from fastapi import HTTPException
from sqlalchemy import func, select

from app.models import User
from app.security import create_access_token, hash_password, verify_dummy_password, verify_password
from app.services.common import commit_or_409


def register(db, data):
    if db.scalar(select(User.id).where(func.lower(User.username) == data.username.lower())) is not None:
        raise HTTPException(status_code=409, detail="Username already taken")
    if db.scalar(select(User.id).where(func.lower(User.email) == str(data.email).lower())) is not None:
        raise HTTPException(status_code=409, detail="Email already registered")
    user = User(username=data.username, email=str(data.email), password_hash=hash_password(data.password))
    db.add(user)
    commit_or_409(db, "Username or email already in use")
    return user


def login(db, data):
    user = db.scalar(select(User).where(func.lower(User.username) == data.username.lower()))
    if user is None:
        verify_dummy_password(data.password)
    elif verify_password(data.password, user.password_hash):
        return {"access_token": create_access_token(user), "token_type": "bearer"}
    raise HTTPException(
        status_code=401,
        detail="Invalid username or password",
        headers={"WWW-Authenticate": "Bearer"},
    )
