from firebase.firebase import get_firestore_client
from google.cloud import firestore
from datetime import datetime, timezone
from app.guesses.repository import GuessResponse

db = get_firestore_client()
guesses_ref = db.collection("guesses")

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