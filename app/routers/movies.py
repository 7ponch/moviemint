from typing import Literal, Optional
from fastapi import APIRouter, Depends
from app.database import get_db
from app.dependencies import get_current_user
from app.schemas.movie import MovieCreate, MovieUpdate, MovieOut
from app.services import movie_service

router = APIRouter(prefix="/movies", tags=["movies"])


@router.get("", response_model=list[MovieOut])
def list_movies(
    genre: Optional[str] = None,
    q: Optional[str] = None,
    section: Optional[Literal["mainstream", "hidden_gem"]] = None,
    db=Depends(get_db),
):
    return movie_service.list_movies(db, genre, q, section)


@router.get("/random", response_model=MovieOut)
def random_movie(genre: Optional[str] = None, current_user=Depends(get_current_user), db=Depends(get_db)):
    return movie_service.get_random_movie(db, current_user.id, genre)


@router.get("/{movie_id}", response_model=MovieOut)
def get_movie(movie_id: int, db=Depends(get_db)):
    return movie_service.get_movie(db, movie_id)


@router.post("", response_model=MovieOut, status_code=201, dependencies=[Depends(get_current_user)])
def create_movie(data: MovieCreate, db=Depends(get_db)):
    return movie_service.create_movie(db, data)


@router.patch("/{movie_id}", response_model=MovieOut, dependencies=[Depends(get_current_user)])
def update_movie(movie_id: int, data: MovieUpdate, db=Depends(get_db)):
    return movie_service.update_movie(db, movie_id, data)


@router.delete("/{movie_id}", status_code=204, dependencies=[Depends(get_current_user)])
def delete_movie(movie_id: int, db=Depends(get_db)):
    movie_service.delete_movie(db, movie_id)
