from pydantic import BaseModel

class GuessRequest(BaseModel):
    guess: str

class GuessResponse(BaseModel):
    guess: str
    is_correct: bool
    guesses_left: int
    score: int