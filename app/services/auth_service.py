import hashlib
import hmac
import os
import secrets

from fastapi import HTTPException
from app import storage

ITERATIONS = 100_000


def hash_password(password):
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, ITERATIONS)
    return salt.hex() + ":" + digest.hex()


def verify_password(password, stored):
    salt_hex, digest_hex = stored.split(":")
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), ITERATIONS)
    return hmac.compare_digest(digest.hex(), digest_hex)


def register(data):
    for user in storage.users.values():
        if user["username"].lower() == data.username.lower():
            raise HTTPException(status_code=409, detail="Username already taken")
        if user["email"].lower() == str(data.email).lower():
            raise HTTPException(status_code=409, detail="Email already registered")
    user_id = storage.next_id("user")
    user = {
        "id": user_id,
        "username": data.username,
        "email": str(data.email),
        "password_hash": hash_password(data.password),
    }
    storage.users[user_id] = user
    return user


def login(data):
    for user in storage.users.values():
        if user["username"].lower() == data.username.lower():
            if verify_password(data.password, user["password_hash"]):
                token = secrets.token_hex(16)
                storage.tokens[token] = user["id"]
                return {"access_token": token, "token_type": "bearer"}
            break
    raise HTTPException(status_code=401, detail="Invalid username or password")