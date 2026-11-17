from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class WatchlistCreate(BaseModel):
    movie_id: int = Field(gt=0)
    status: Literal["planned", "watched"] = "planned"


class WatchlistUpdate(BaseModel):
    status: Literal["planned", "watched"]


class WatchlistOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    movie_id: int
    status: Literal["planned", "watched"]
