from pydantic import BaseModel

class Song(BaseModel):
    id: str
    title: str
    artist: str
    instrument: str
    clip_url: str
    credit_clip: str
