import json
from app.songs.consts import SONGS_METADATA_FILE
from typing import List, Dict

def load_songs_metadata() -> List[Dict]:
    with open(SONGS_METADATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def get_song_by_id(song_id: str) -> Dict:
    songs = load_songs_metadata()
    for song in songs:
        if song["id"] == song_id:
            return song
    return None