from typing import Literal, Optional
from pydantic import BaseModel, Field


class MovieCreate(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    year: int = Field(ge=1888, le=2100)
    genre: str = Field(min_length=1, max_length=50)
    description: str = Field(default="", max_length=1000)
    poster_url: Optional[str] = None
    trailer_url: Optional[str] = None
    section: Literal["mainstream", "hidden_gem"] = "mainstream"


class MovieUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=100)
    year: Optional[int] = Field(default=None, ge=1888, le=2100)
    genre: Optional[str] = Field(default=None, min_length=1, max_length=50)
    description: Optional[str] = Field(default=None, max_length=1000)
    poster_url: Optional[str] = None
    trailer_url: Optional[str] = None
    section: Optional[Literal["mainstream", "hidden_gem"]] = None


class MovieOut(MovieCreate):
    id: int
    rating: float
    reviews_count: int