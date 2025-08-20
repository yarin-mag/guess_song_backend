from firebase.firebase import get_firestore_client
from google.cloud import firestore
from datetime import datetime, timezone, date
from app.guesses.repository import GuessResponse

db = get_firestore_client()
guesses_ref = db.collection("guesses")

_cached_guesses = {}
_cache_date = None


async def add_guess(user_id: str, guess: str, song_id: str, is_correct: bool, score: int) -> None:
    data = {
        "user_id": user_id,
        "song_id": song_id,
        "is_correct": is_correct,
        "guess": guess,
        "score": score,
        "timestamp": firestore.SERVER_TIMESTAMP,
    }
    await guesses_ref.add(data)

async def get_guesses(user_id: str):
    now = datetime.now(timezone.utc)
    
    start_of_day = datetime(year=now.year, month=now.month, day=now.day, tzinfo=timezone.utc)
    query = guesses_ref.where("user_id", "==", user_id).where("timestamp", ">=", start_of_day)
    docs = query.stream()
    guesses = []
    async for doc in docs:
        data = doc.to_dict()
        guesses.append(
            GuessResponse(
                guess=data.get("guess", ""),
                is_correct=data.get("is_correct", False),
                score=data.get("score", 0),
                guesses_left=data.get("guesses_left", 0)
            )
        )
    return guesses

def clean_cache_not_from_today():
    global _cached_guesses, _cache_date
    now = datetime.now(timezone.utc)
    today = now.date()

    if _cache_date != today:
        _cached_guesses = {}
        _cache_date = today

async def get_cached_guess_of_today(guess: str):
    global _cached_guesses, _cache_date
    now = datetime.now(timezone.utc)
    clean_cache_not_from_today()
    
    if guess in _cached_guesses:
        return (_cached_guesses[guess], True)

    start_of_day = datetime(year=now.year, month=now.month, day=now.day, tzinfo=timezone.utc)
    query = guesses_ref.where("guess", "==", guess).where("timestamp", ">=", start_of_day)
    docs = query.stream()
    async for doc in docs:
        data = doc.to_dict()
        score = data.get("score", None)
        _cached_guesses[guess] = score
        return (score, True)
        
    return (None, False)

async def cache_guess(guess: str, score: int):
    global _cached_guesses
    _cached_guesses[guess] = score