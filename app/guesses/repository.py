from pydantic import BaseModel

class GuessRequest(BaseModel):
    guess: str

from typing import Optional

class GuessResponse(BaseModel):
    guess: str
    is_correct: bool
    guesses_left: int
    score: int
    credit_url: Optional[str] = None