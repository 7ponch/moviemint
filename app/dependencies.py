from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app import storage 

bearer_schema = HTTPBearer(auto_error=False)

def get_current_user(credentials:HTTPAuthorizationCredentials = Depends(bearer_schema)):
    if credentials is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    user_id = storage.tokens.get(credentials.credentials)
    if user_id is None or user_id  not in storage.users:
        raise HTTPException(status_code=401, detail="Invalid token")
    return storage.users[user_id]