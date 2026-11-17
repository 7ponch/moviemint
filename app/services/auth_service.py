import hashlib
import hmac
import os
import secrets

from fastapi import HTTPException
from sqlalchemy import func, select

from app.models import AuthToken, User
from app.services.common import commit_or_409

ITERATIONS = 100_000


def hash_password(password):
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, ITERATIONS)
    return salt.hex() + ":" + digest.hex()


def verify_password(password, stored):
    salt_hex, digest_hex = stored.split(":")
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), ITERATIONS)
    return hmac.compare_digest(digest.hex(), digest_hex)


def hash_token(token):
    return hashlib.sha256(token.encode()).hexdigest()


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
    if user is not None and verify_password(data.password, user.password_hash):
        token = secrets.token_hex(32)
        db.add(AuthToken(token_hash=hash_token(token), user_id=user.id))
        db.commit()
        return {"access_token": token, "token_type": "bearer"}
    raise HTTPException(status_code=401, detail="Invalid username or password")
