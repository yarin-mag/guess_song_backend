from app.guesses.consts import MAX_DAILY_GUESSES_FREE_USER, MAX_DAILY_GUESSES_PREMIUM
from app.guesses.model import add_guess, get_guesses
from app.guesses.repository import GuessRequest, GuessResponse
from datetime import datetime
from .logic import get_similarity_score
from google.cloud import firestore
import time
from app.shared.http import call_internal_service

# Cache state
_cached_daily_song = None
_cached_epoch = 0

async def get_cached_daily_song():
    global _cached_daily_song, _cached_epoch
    now = time.time()
    today_epoch = int(now - (now % 86400))
    if _cached_daily_song and _cached_epoch == today_epoch:
        return _cached_daily_song

    # Fetch from songs service
    song = await call_internal_service("/songs/daily")
    _cached_daily_song = song
    _cached_epoch = today_epoch
    return song

async def is_guess_correct(user_guess: str, daily_song: dict) -> bool:
    score = await get_similarity_score(user_guess, daily_song)
    return score

async def make_guess(user_id: str, body: GuessRequest) -> GuessResponse:
    user = await call_internal_service("/users", "GET", None, { "user_id": user_id })
    if not user:
        raise Exception("User not found")
    user_new_guess = body["guess"]
    daily_song = await get_cached_daily_song()
    
    today = datetime.utcnow().date().isoformat()
    guesses_user_made_today = await get_guesses(user_id, date=today)
    for past_guess in guesses_user_made_today:
        if past_guess["guess"] == user_new_guess:
            return GuessResponse(guess=user_new_guess, is_correct=past_guess["is_correct"], score=past_guess['score'], guesses_left=user.get("guesses_left"))

    score = await is_guess_correct(user_new_guess, daily_song)

    user_guesses = user.get("guesses", {})
    guesses_made_today = user_guesses.get(today, 0)
    guesses_user_allowed_to_make_today = MAX_DAILY_GUESSES_PREMIUM if user.get("is_subscribed") else MAX_DAILY_GUESSES_FREE_USER
    if guesses_made_today >= guesses_user_allowed_to_make_today:
        raise Exception("No guesses left for today")
    
    is_correct = score == 1000
    
    await add_guess(user_id, user_new_guess, daily_song["id"], is_correct, score)
    updated_guesses = {**user_guesses, today: guesses_made_today + 1}
    guesses_left = guesses_user_allowed_to_make_today - updated_guesses[today]
    
    await call_internal_service(
    "/users",
    "PUT",
    {
        **user,
        "guesses": updated_guesses,
        "guesses_left": guesses_left,
        "last_guess_date": datetime.utcnow().isoformat()
    },
    { "user_id": user_id }
)

    return GuessResponse(guess=user_new_guess, is_correct=is_correct, score=score, guesses_left=guesses_left)


async def get_user_guesses(user_id: str) -> list[GuessResponse]:
    return await get_guesses(user_id)