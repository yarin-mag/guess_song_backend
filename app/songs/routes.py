from fastapi import APIRouter, Request
from app.songs.service import get_random_song, get_song
from fastapi.responses import JSONResponse
from .service import get_daily_song

router = APIRouter(prefix="/songs", tags=["songs"])

@router.get("/daily")
async def daily_song(request: Request):
    auth_type = request.get("state", {}).get("auth_type", None)
    should_get_credit_url = "internal" == auth_type
    return await get_daily_song(should_get_credit_url)

@router.get("/random")
async def get_random():
    """
    Returns a random song from the list.
    """
    return get_random_song()

@router.get("/{song_id}")
async def get_by_id(song_id: str):
    """
    Returns metadata for a specific song.
    """
    song = get_song(song_id)
    return JSONResponse(song)