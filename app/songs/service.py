from app.songs.model import load_songs_metadata, get_song_by_id
from typing import Dict
import random

def get_random_song() -> Dict:
    songs = load_songs_metadata()
    return random.choice(songs)

def get_song(song_id: str) -> Dict:
    song = get_song_by_id(song_id)
    if not song:
        raise Exception("Song not found")
    return song