from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.database import get_db
from app.models import User
from app.security import TokenError, TokenExpired, decode_access_token

bearer_scheme = HTTPBearer(auto_error=False)


def _unauthorized(detail):
    return HTTPException(status_code=401, detail=detail, headers={"WWW-Authenticate": "Bearer"})


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db=Depends(get_db),
):
    if credentials is None:
        raise _unauthorized("Not authenticated")
    try:
        user_id = decode_access_token(credentials.credentials)
    except TokenExpired:
        raise _unauthorized("Token expired")
    except TokenError:
        raise _unauthorized("Invalid token")
    user = db.get(User, user_id)
    if user is None:
        raise _unauthorized("Invalid token")
    return user


def require_admin(current_user=Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user
