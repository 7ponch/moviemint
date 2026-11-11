from fastapi import APIRouter, Depends
from app.dependencies import get_current_user
from app.schemas.reviews import ReviewCreate, ReviewUpdate, ReviewOut
from app.services import review_service

router = APIRouter(tags=["reviews"])


@router.post("/movies/{movie_id}/reviews", response_model=ReviewOut, status_code=201)
def create_review(movie_id: int, data: ReviewCreate, current_user=Depends(get_current_user)):
    return review_service.create_review(movie_id, current_user["id"], data)


@router.get("/movies/{movie_id}/reviews", response_model=list[ReviewOut])
def list_reviews(movie_id: int):
    return review_service.list_reviews(movie_id)


@router.patch("/reviews/{review_id}", response_model=ReviewOut)
def update_review(review_id: int, data: ReviewUpdate, current_user=Depends(get_current_user)):
    return review_service.update_review(review_id, current_user["id"], data)


@router.delete("/reviews/{review_id}", status_code=204)
def delete_review(review_id: int, current_user=Depends(get_current_user)):
    review_service.delete_review(review_id, current_user["id"])