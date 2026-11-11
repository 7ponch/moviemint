from typing import Optional
from fastapi import APIRouter, Depends
from app.dependencies import get_current_user
from app.schemas.movie import MovieCreate, MovieUpdate, MovieOut
from app.services import movie_service

router = APIRouter(prefix="/movies", tags=["movies"])


@router.get("", response_model=list[MovieOut])
def list_movies(genre: Optional[str] = None, q: Optional[str] = None, section: Optional[str] = None):
    return movie_service.list_movies(genre, q, section)


@router.get("/random", response_model=MovieOut)
def random_movie(genre: Optional[str] = None, current_user=Depends(get_current_user)):
    return movie_service.get_random_movie(current_user["id"], genre)


@router.get("/{movie_id}", response_model=MovieOut)
def get_movie(movie_id: int):
    return movie_service.get_movie(movie_id)


@router.post("", response_model=MovieOut, status_code=201, dependencies=[Depends(get_current_user)])
def create_movie(data: MovieCreate):
    return movie_service.create_movie(data)


@router.patch("/{movie_id}", response_model=MovieOut, dependencies=[Depends(get_current_user)])
def update_movie(movie_id: int, data: MovieUpdate):
    return movie_service.update_movie(movie_id, data)


@router.delete("/{movie_id}", status_code=204, dependencies=[Depends(get_current_user)])
def delete_movie(movie_id: int):
    movie_service.delete_movie(movie_id)