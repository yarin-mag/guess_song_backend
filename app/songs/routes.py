from fastapi import APIRouter, Request, Depends
from app.songs.service import get_random_song, get_song, get_populated_daily_song, check_if_user_won, get_winner_song
from fastapi.responses import JSONResponse
from .service import get_daily_song
from app.shared.dependencies import get_internal_service_user

router = APIRouter(prefix="/songs", tags=["songs"])

@router.get("/winner")
async def winner_song(request: Request, identity=Depends(get_internal_service_user())):
    shall_pass = False
    is_machine = bool(identity.get("service_id"))
    is_user = bool(identity.get("user_id"))
    did_user_win = False
    
    if is_user:
        did_user_win = await check_if_user_won(identity.get("user_id"))
        
    shall_pass = did_user_win or is_machine
    res = {}
    if shall_pass:
        res = JSONResponse(await get_winner_song())
    return res

@router.get("/daily")
async def daily_song(request: Request):
    return await get_daily_song()

@router.get("/daily-populated")
async def daily_song_populated(request: Request, identity=Depends(get_internal_service_user())):
    return await get_populated_daily_song()

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