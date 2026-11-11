from typing import Optional
from pydantic import BaseModel, Field


class ReviewCreate(BaseModel):
    rating: int = Field(ge=1, le=10)
    text: str = Field(default="", max_length=1000)


class ReviewUpdate(BaseModel):
    rating: Optional[int] = Field(default=None, ge=1, le=10)
    text: Optional[str] = Field(default=None, max_length=1000)


class ReviewOut(BaseModel):
    id: int
    user_id: int
    movie_id: int
    rating: int
    text: str