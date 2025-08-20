from app.guesses.consts import MAX_DAILY_GUESSES_FREE_USER, MAX_DAILY_GUESSES_PREMIUM
from app.guesses.model import add_guess, get_guesses, get_cached_guess_of_today, cache_guess
from app.guesses.repository import GuessRequest, GuessResponse
from datetime import datetime, timedelta
from .logic import get_similarity_score
import time
from app.shared.http import call_internal_service
from app.shared.exceptions import UserNotFoundException, NoGuessesLeftException

# Cache state
_cached_daily_song = None
_cached_epoch = 0

async def get_cached_winner_song():
    global _cached_daily_song, _cached_epoch
    now = time.time()
    today_epoch = int(now - (now % 86400))
    if _cached_daily_song and _cached_epoch == today_epoch:
        return _cached_daily_song

    # Fetch from songs service
    song = await call_internal_service("/songs/winner")
    _cached_daily_song = song
    _cached_epoch = today_epoch
    return song

async def is_guess_correct(user_guess: str, daily_song: dict) -> bool:
    (score, is_cached_from_today) = await get_cached_guess_of_today(user_guess)
    if is_cached_from_today:
        return score
    
    score = await get_similarity_score(user_guess, daily_song)
    await cache_guess(user_guess, score)
    return score

async def make_guess(user_id: str, body: GuessRequest) -> GuessResponse:
    user = await call_internal_service("/users", "GET", None, { "user_id": user_id })
    if not user:
        raise UserNotFoundException()
    user_new_guess = body["guess"]
    daily_song = await get_cached_winner_song()
    
    today = datetime.utcnow().date().isoformat()
    yesterday = (datetime.utcnow() - timedelta(days=1)).date().isoformat()
    guesses_user_made_today = await get_guesses(user_id)
    for past_guess in list(guesses_user_made_today):
        if past_guess.guess == user_new_guess:
            return GuessResponse(guess=user_new_guess, is_correct=past_guess.is_correct, score=past_guess.score, guesses_left=user.get("guesses_left"), credit_url=past_guess.credit_url)

    user_guesses = user.get("guesses", {})
    guesses_made_today = user_guesses.get(today, 0)
    guesses_user_allowed_to_make_today = MAX_DAILY_GUESSES_PREMIUM if user.get("is_subscribed") else MAX_DAILY_GUESSES_FREE_USER
    if guesses_made_today >= guesses_user_allowed_to_make_today:
        raise NoGuessesLeftException()
    
    score = await is_guess_correct(user_new_guess, daily_song)
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
        "last_guess_date": datetime.utcnow().isoformat(),
        "last_time_guessed_right": today if is_correct else yesterday
    },
    { "user_id": user_id }
)

    credit_url = None
    title = None
    artist = None
    if is_correct:
        credit_url = daily_song.get("credit_clip")
        artist = daily_song.get("artist")
        title = daily_song.get("title")

    return GuessResponse(guess=user_new_guess, is_correct=is_correct, score=score, guesses_left=guesses_left, credit_url=credit_url, title=title, artist=artist)


async def get_user_guesses(user_id: str) -> list[GuessResponse]:
    return await get_guesses(user_id)