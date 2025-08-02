from firebase.firebase import get_firestore_client
from google.cloud import firestore
from datetime import datetime, timedelta
import random

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

async def get_daily_song(should_get_credit_url: bool):
    global _daily_song_cache
    now = datetime.utcnow()

    # Check if cached value is still valid
    if _daily_song_cache["value"] and _daily_song_cache["expires_at"] > now:
        return _daily_song_cache["value"]

    today_str = now.date().isoformat()
    query = songs_ref.where("date_used", "==", today_str)
    docs = query.stream()
    async for doc in docs:
        song = doc.to_dict()
        _daily_song_cache = {
            "value": song,
            "expires_at": _next_utc_midnight()
        }
        return song

    # No song for today, pick a new one
    docs = [doc async for doc in songs_ref.stream()]
    unused_docs = [doc for doc in docs if not doc.to_dict().get("date_used")]

    if not unused_docs:
        raise Exception("No unused songs left")

    new_daily_song_doc = random.choice(unused_docs)
    await new_daily_song_doc.reference.update({"date_used": today_str})
    song = new_daily_song_doc.to_dict()

    _daily_song_cache = {
        "value": song,
        "expires_at": _next_utc_midnight()
    }

    return song

async def get_random_song():
    docs = [doc async for doc in songs_ref.stream()]
    if not docs:
        return None
    return random.choice(docs).to_dict()
