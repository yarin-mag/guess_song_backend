from app.songs.model import (
    get_daily_song as get_daily_song_from_db,
    get_random_song as get_random_song_from_db,
    get_song_by_id as get_song_by_id_from_db,
)
from typing import Dict
from app.shared.http import call_internal_service
from app.shared.exceptions import SongNotFoundException
from datetime import datetime


async def check_if_user_won(user_id) -> bool:
    if not user_id:
        return False

    user = await call_internal_service("/users", "GET", None, {"user_id": user_id})
    if not user:
        return False

    today = datetime.utcnow().date().isoformat()
    return user.get("last_time_guessed_right") == today


async def get_winner_song() -> Dict:
    songs = await get_daily_song_from_db()
    song_today = songs.get("today")

    song_to_return = None

    if song_today:
        song_to_return = {
            "id": song_today.get("id"),
            "title": song_today.get("title"),
            "artist": song_today.get("artist"),
            "clip_url": song_today.get("clip_url"),
            "credit_clip": song_today.get("credit_clip"),
        }

    return song_to_return


async def get_daily_song() -> Dict:
    songs = await get_daily_song_from_db()
    song_today = songs.get("today")
    song_yesterday = songs.get("yesterday")

    song_to_return = {"today": None, "yesterday": None}

    if song_today:
        today_data = {
            "clip_url": song_today.get("clip_url"),
            "id": song_today.get("id"),
        }
        song_to_return["today"] = today_data

    if song_yesterday:
        yesterday_data = {
            "title": song_yesterday.get("title"),
            "artist": song_yesterday.get("artist"),
            "credit_clip": song_yesterday.get("credit_clip"),
        }
        song_to_return["yesterday"] = yesterday_data

    return song_to_return


async def get_populated_daily_song() -> Dict:
    songs = await get_daily_song_from_db()
    song_today = songs.get("today")

    song_to_return = {}

    if song_today:
        song_to_return["id"] = song_today.get("id")
        song_to_return["clip_url"] = song_today.get("clip_url")
        song_to_return["title"] = song_today.get("title")
        song_to_return["artist"] = song_today.get("artist")
        song_to_return["credit_clip"] = song_today.get("credit_clip")

    return song_to_return


async def get_random_song() -> Dict:
    return await get_random_song_from_db()


async def get_song(song_id: str) -> Dict:
    song = await get_song_by_id_from_db(song_id)
    if not song:
        raise SongNotFoundException()
    return song
