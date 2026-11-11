from fastapi import APIRouter, Depends
from app.dependencies import get_current_user
from app.schemas.user import UserOut, UserUpdate
from app.services import user_service

router = APIRouter(tags=["users"])


@router.get("/users/{user_id}", response_model=UserOut)
def get_user(user_id: int):
    return user_service.get_user(user_id)


@router.patch("/me", response_model=UserOut)
def update_me(data: UserUpdate, current_user=Depends(get_current_user)):
    return user_service.update_user(current_user["id"], data)


@router.delete("/me", status_code=204)
def delete_me(current_user=Depends(get_current_user)):
    user_service.delete_user(current_user["id"])