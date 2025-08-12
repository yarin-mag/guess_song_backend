# import os
# from openai import AsyncOpenAI
# from dotenv import load_dotenv
# load_dotenv()


# client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# async def get_similarity_score(guess: str, correct_song: dict) -> int:
#     prompt = (
#         f"Act as a person who plays 'guess my chosen songs' with someone. "
#         f"You chose the song '{correct_song['title']}' by {correct_song['artist']} and now the person gave you his guess which is: '{guess}'. "
#         f"Return a score between 0 and 1000 such that a higher score means the guess is closer. "
#         f"Return 1000 only if the guess matches the actual song (you can tolerate small typos). "
#         f"If they guess a similar song or correct artist, score should be high but not 1000. "
#         f"If it’s completely off, score low."
#         f"Notice - RETURN ONLY THE NUMBER."
#     )

#     response = await client.chat.completions.create(
#         model="gpt-3.5-turbo",  # the cheapest model
#         messages=[{"role": "user", "content": prompt}],
#         max_tokens=10,
#     )

#     content = response.choices[0].message.content.strip()
#     digits = "".join(filter(str.isdigit, content))
#     return max(0, min(1000, int(digits or 0)))

import os, json, re, unicodedata
from openai import AsyncOpenAI
from rapidfuzz.distance import Levenshtein

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def norm(s: str) -> str:
    s = s.lower()
    s = unicodedata.normalize("NFKD", s)
    s = re.sub(r"\(.*?\)|\[.*?\]", "", s)  # remove (...) and [...]
    s = re.sub(r"\b(remaster(ed)?|live|feat\.?|ft\.?)\b", "", s)
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def norm_dist(a: str, b: str) -> float:
    if not a or not b: return 1.0
    return Levenshtein.normalized_distance(a, b)  # 0 identical … 1 different

async def get_similarity_score(guess: str, correct: dict) -> int:
    title = correct["title"]; artist = correct["artist"]
    n_title, n_artist = norm(title), norm(artist)

    # crude parse from guess like "Song - Artist" or "Artist - Song"
    g = norm(guess)
    parts = [p.strip() for p in re.split(r"[-–|:]", g)]
    # heuristic: try both interpretations
    candidates = []
    if len(parts) == 1:
        candidates.append({"g_title": parts[0], "g_artist": ""})
    else:
        for i in range(len(parts)):
            left = " ".join(parts[:i+1]); right = " ".join(parts[i+1:])
            candidates.append({"g_title": left, "g_artist": right})
            candidates.append({"g_title": right, "g_artist": left})

    best = {"score": 0}
    for c in candidates:
        tdist = norm_dist(c["g_title"], n_title)
        adist = norm_dist(c["g_artist"], n_artist)
        title_exact = tdist <= 0.08
        artist_exact = adist <= 0.08

        # Hard rule: exact ⇒ 1000
        if title_exact and artist_exact:
            return 1000

        # Prepare LLM call with signals
        system = """You are a strict song-guess evaluator. Follow the rubric exactly.
Output ONLY valid JSON: {"match_type": "...", "reasoning": "...", "score": <0-1000>}"""

        user = f"""
Correct song:
- title: "{title}"
- artist: "{artist}"

User guess (interpreted):
- title: "{c['g_title']}"
- artist: "{c['g_artist']}"

Precomputed signals:
- title_edit_distance_norm: {tdist:.3f}
- artist_edit_distance_norm: {adist:.3f}
- title_exact: {str(title_exact).lower()}
- artist_exact: {str(artist_exact).lower()}

[Rubric as above... trimmed for brevity]
"""

        resp = await client.chat.completions.create(
            model="gpt-4o-mini",          # small + steadier than 3.5; use what you have
            temperature=0,
            top_p=0.1,
            messages=[{"role":"system","content":system},{"role":"user","content":user}],
            max_tokens=100,
            response_format={"type":"json_object"}
        )
        obj = json.loads(resp.choices[0].message.content)
        s = int(obj.get("score", 0))

        # Post caps/floors:
        if artist_exact and not title_exact and tdist > 0.25:
            s = min(s, 850)
        if not artist_exact and not title_exact and tdist > 0.35 and adist > 0.35:
            s = min(s, 300)
        if s > best["score"]:
            best = {"score": s}

    # Make sure within bounds
    return max(0, min(1000, best["score"]))
