from typing import Optional
from fastapi import APIRouter, Depends
from app.dependencies import get_current_user
from app.schemas.watchlist import WatchlistCreate, WatchlistUpdate, WatchlistOut
from app.services import watchlist_service

router = APIRouter(prefix="/me/watchlist", tags=["watchlist"])


@router.post("", response_model=WatchlistOut, status_code=201)
def add_to_watchlist(data: WatchlistCreate, current_user=Depends(get_current_user)):
    return watchlist_service.add_item(current_user["id"], data)


@router.get("", response_model=list[WatchlistOut])
def list_watchlist(status: Optional[str] = None, current_user=Depends(get_current_user)):
    return watchlist_service.list_items(current_user["id"], status)


@router.patch("/{movie_id}", response_model=WatchlistOut)
def update_status(movie_id: int, data: WatchlistUpdate, current_user=Depends(get_current_user)):
    return watchlist_service.update_status(current_user["id"], movie_id, data)


@router.delete("/{movie_id}", status_code=204)
def remove_from_watchlist(movie_id: int, current_user=Depends(get_current_user)):
    watchlist_service.remove_item(current_user["id"], movie_id)