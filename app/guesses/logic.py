import os
from openai import AsyncOpenAI
from dotenv import load_dotenv
load_dotenv()


client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def get_similarity_score(guess: str, correct_song: dict) -> int:
    prompt = (
        f"Act as a person who plays 'guess my chosen songs' with someone. "
        f"You chose the song '{correct_song['title']}' by {correct_song['artist']} and now the person gave you his guess which is: '{guess}'. "
        f"Return a score between 0 and 1000 such that a higher score means the guess is closer. "
        f"Return 1000 only if the guess matches the actual song (you can tolerate small typos). "
        f"If they guess a similar song or correct artist, score should be high but not 1000. "
        f"If it’s completely off, score low."
        f"Notice - RETURN ONLY THE NUMBER."
    )

    response = await client.chat.completions.create(
        model="gpt-3.5-turbo",  # the cheapest model
        messages=[{"role": "user", "content": prompt}],
        max_tokens=10,
    )

    content = response.choices[0].message.content.strip()
    digits = "".join(filter(str.isdigit, content))
    return max(0, min(1000, int(digits or 0)))
