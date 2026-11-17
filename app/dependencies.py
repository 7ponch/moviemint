from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select

from app.database import get_db
from app.models import AuthToken, User
from app.services.auth_service import hash_token

bearer_schema = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_schema),
    db=Depends(get_db),
):
    if credentials is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    stmt = (
        select(User)
        .join(AuthToken, AuthToken.user_id == User.id)
        .where(AuthToken.token_hash == hash_token(credentials.credentials))
    )
    user = db.scalar(stmt)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user
