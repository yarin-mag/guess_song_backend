import json
import os
import time
import random

SONGS_FILE = "app/static/songs.json"
DAILY_SONG_FILE = "app/static/daily_song.json"

def _load_songs():
    with open(SONGS_FILE, "r") as f:
        return json.load(f)

def _save_songs(songs):
    with open(SONGS_FILE, "w") as f:
        json.dump(songs, f, indent=2)

def _get_today_epoch():
    now = time.time()
    return int(now - (now % 86400))

def get_daily_song():
    # 1. Try to load daily song cache
    today_epoch = _get_today_epoch()
    if os.path.exists(DAILY_SONG_FILE):
        with open(DAILY_SONG_FILE, "r") as f:
            data = json.load(f)
            if data.get("epoch") == today_epoch:
                return data["song"]

    # 2. Pick new song and mark as used
    songs = _load_songs()
    unused_songs = [s for s in songs if not s.get("is_used", False)]
    if not unused_songs:
        raise Exception("No unused songs left")

    new_song = random.choice(unused_songs)
    new_song["is_used"] = True
    _save_songs(songs)

    with open(DAILY_SONG_FILE, "w") as f:
        json.dump({"epoch": today_epoch, "song": new_song}, f, indent=2)

    return new_song
