from fastapi import APIRouter, Depends
from app.dependencies import get_current_user
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse
from app.schemas.user import UserOut
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=201)
def register(data: RegisterRequest):
    return auth_service.register(data)


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest):
    return auth_service.login(data)


@router.get("/me", response_model=UserOut)
def me(current_user=Depends(get_current_user)):
    return current_user