from app.shared.exceptions import NoUnusedSongsException
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

def get_daily_song(should_get_credit_url: bool):
    # 1. Try to load daily song cache
    today_epoch = _get_today_epoch()
    if os.path.exists(DAILY_SONG_FILE):
        with open(DAILY_SONG_FILE, "r") as f:
            data = json.load(f)
            if data.get("epoch") == today_epoch:
                song_data = {"clip_url": data["song"]["clip_url"]}
                if should_get_credit_url:
                    song_data["credit_clip"] = data["song"]["credit_clip"]
                return song_data

    # 2. Pick new song and mark as used
    songs = _load_songs()
    unused_songs = [s for s in songs if not s.get("is_used", False)]
    if not unused_songs:
        raise NoUnusedSongsException()

    new_song = random.choice(unused_songs)
    new_song["is_used"] = True
    _save_songs(songs)

    with open(DAILY_SONG_FILE, "w") as f:
        json.dump({"epoch": today_epoch, "song": new_song}, f, indent=2)

    song_data = {"clip_url": new_song["clip_url"]}
    if should_get_credit_url:
        song_data["credit_clip"] = new_song["credit_clip"]
    return song_data
