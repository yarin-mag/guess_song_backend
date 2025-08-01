from fastapi import APIRouter, Depends, Request
from app.guesses.repository import GuessRequest, GuessResponse
from app.guesses.service import make_guess
from app.shared.dependencies import get_current_user
from app.middlewares.route_rate_limiter import rate_limited
from app.guesses.service import get_user_guesses

router = APIRouter(prefix="/guesses", tags=["guesses"])

@router.post("", response_model=GuessResponse)
@rate_limited(limit=10, window=60)  # 10 guesses per minute per user
async def guess_song(
    request: Request,
    user=Depends(get_current_user(False))
):
    return await make_guess(user["user_id"], await request.json())

@router.get("/history", response_model=list[GuessResponse])
async def guess_history(user=Depends(get_current_user(allow_unauthenticated=False))):
    return await get_user_guesses(user["user_id"])
