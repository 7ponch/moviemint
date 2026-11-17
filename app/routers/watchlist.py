from typing import Literal, Optional
from fastapi import APIRouter, Depends
from app.database import get_db
from app.dependencies import get_current_user
from app.schemas.watchlist import WatchlistCreate, WatchlistUpdate, WatchlistOut
from app.services import watchlist_service

router = APIRouter(prefix="/me/watchlist", tags=["watchlist"])


@router.post("", response_model=WatchlistOut, status_code=201)
def add_to_watchlist(data: WatchlistCreate, current_user=Depends(get_current_user), db=Depends(get_db)):
    return watchlist_service.add_item(db, current_user.id, data)


@router.get("", response_model=list[WatchlistOut])
def list_watchlist(
    status: Optional[Literal["planned", "watched"]] = None,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    return watchlist_service.list_items(db, current_user.id, status)


@router.patch("/{movie_id}", response_model=WatchlistOut)
def update_status(movie_id: int, data: WatchlistUpdate, current_user=Depends(get_current_user), db=Depends(get_db)):
    return watchlist_service.update_status(db, current_user.id, movie_id, data)


@router.delete("/{movie_id}", status_code=204)
def remove_from_watchlist(movie_id: int, current_user=Depends(get_current_user), db=Depends(get_db)):
    watchlist_service.remove_item(db, current_user.id, movie_id)
