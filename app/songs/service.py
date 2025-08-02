from app.songs.model import get_daily_song as get_daily_song_from_db, get_random_song as get_random_song_from_db, get_song_by_id as get_song_by_id_from_db
from typing import Dict

async def get_daily_song(should_get_credit_url: bool) -> Dict:
    song = await get_daily_song_from_db(should_get_credit_url)
    song_to_return = {"clip_url": song.get("clip_url")}
    if should_get_credit_url:
        song_to_return["credit_clip"] = song.get("credit_clip")
    return song_to_return

async def get_random_song() -> Dict:
    return await get_random_song_from_db()

async def get_song(song_id: str) -> Dict:
    song = await get_song_by_id_from_db(song_id)
    if not song:
        raise Exception("Song not found")
    return song
