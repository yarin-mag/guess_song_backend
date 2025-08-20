from firebase.firebase import get_firestore_client
from google.cloud import firestore
from datetime import datetime, timedelta
import random
from app.shared.exceptions import NoUnusedSongsException

db = get_firestore_client()
songs_ref = db.collection("songs")

# Simple in-memory cache
_daily_song_cache = {
    "value": None,
    "expires_at": None
}

def _next_utc_midnight():
    now = datetime.utcnow()
    tomorrow = now + timedelta(days=1)
    return datetime(tomorrow.year, tomorrow.month, tomorrow.day)

async def get_song_by_id(song_id: str):
    doc = await songs_ref.document(song_id).get()
    if doc.exists:
        return doc.to_dict()
    return None

async def get_song_by_date(date_str: str):
    """
    Fetches a song from Firestore for a specific date.
    """
    query = songs_ref.where("date_used", "==", date_str)
    docs = query.stream()
    async for doc in docs:
        return doc.to_dict()
    return None

async def get_daily_song():
    global _daily_song_cache
    now = datetime.utcnow()

    # Check if cached value is still valid
    if _daily_song_cache.get("value") and _daily_song_cache.get("expires_at") > now:
        return _daily_song_cache["value"]

    today_str = now.date().isoformat()
    yesterday_str = (now.date() - timedelta(days=1)).isoformat()

    # Fetch today's song
    song_today = await get_song_by_date(today_str)
    if not song_today:
        # No song for today, pick a new one
        docs = [doc async for doc in songs_ref.stream()]
        unused_docs = [doc for doc in docs if not doc.to_dict().get("date_used")]

        if not unused_docs:
            raise NoUnusedSongsException()

        new_daily_song_doc = random.choice(unused_docs)
        await new_daily_song_doc.reference.update({"date_used": today_str})
        song_today = new_daily_song_doc.to_dict()

    # Fetch yesterday's song
    song_yesterday = await get_song_by_date(yesterday_str)

    result = {
        "today": song_today,
        "yesterday": song_yesterday
    }

    _daily_song_cache = {
        "value": result,
        "expires_at": _next_utc_midnight()
    }

    return result

async def get_random_song():
    docs = [doc async for doc in songs_ref.stream()]
    if not docs:
        return None
    return random.choice(docs).to_dict()
