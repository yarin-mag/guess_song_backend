import os, re, json, math, unicodedata
from functools import lru_cache
from typing import Dict, Tuple, List
from rapidfuzz.distance import Levenshtein
from openai import AsyncOpenAI

# ========== OpenAI client ==========
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ========== Text utils ==========
_WORD_SEP = re.compile(r"[-–—|:/]+")
_BY_SPLIT = re.compile(r"\bby\b", re.IGNORECASE)

def _ascii_fold(s: str) -> str:
    # strip accents but keep letters/numbers
    s = unicodedata.normalize("NFKD", s)
    return "".join(ch for ch in s if not unicodedata.combining(ch))

def norm(s: str) -> str:
    if not s:
        return ""
    s = _ascii_fold(s).lower()
    # remove parens/brackets content (remaster, live, feat, etc.)
    s = re.sub(r"\(.*?\)|\[.*?\]", " ", s)
    s = re.sub(r"\b(remaster(?:ed)?|live|acoustic|feat\.?|ft\.?|version|edit|mix|rmx)\b", " ", s)
    # normalize &, and
    s = re.sub(r"\b(&|and)\b", " and ", s)
    # collapse punctuation to spaces
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def nlev(a: str, b: str) -> float:
    """Normalized edit distance: 0=identical, 1=different."""
    if not a or not b:
        return 1.0
    return Levenshtein.normalized_distance(a, b)

def _token_set_ratio(a: str, b: str) -> float:
    """Very simple token overlap (0..1)."""
    A, B = set(a.split()), set(b.split())
    if not A or not B:
        return 0.0
    inter = len(A & B)
    return inter / max(len(A), len(B))

def _candidate_splits(guess_norm: str) -> List[Tuple[str, str]]:
    """
    Try to interpret the guess as (title, artist) in several ways.
    Returns list of (g_title, g_artist).
    """
    cand: List[Tuple[str, str]] = []
    g = guess_norm

    # "title by artist"
    if _BY_SPLIT.search(g):
        left, right = _BY_SPLIT.split(g, maxsplit=1)
        cand.append((left.strip(), right.strip()))

    # "A - B" and variants; also try progressive splits
    parts = [p.strip() for p in _WORD_SEP.split(g) if p.strip()]
    if parts:
        if len(parts) == 1:
            cand.append((parts[0], ""))             # title only
            cand.append(("", parts[0]))             # artist only
        else:
            for i in range(len(parts) - 1):
                left = " ".join(parts[:i+1]).strip()
                right = " ".join(parts[i+1:]).strip()
                cand.append((left, right))          # title - artist
                cand.append((right, left))          # artist - title

    # Fallback whole string as title
    cand.append((g, ""))
    # Dedup while preserving order
    seen = set()
    uniq = []
    for t, a in cand:
        key = (t, a)
        if key not in seen:
            seen.add(key)
            uniq.append(key)
    return uniq

# ========== Embeddings helpers ==========
def _cos(a: List[float], b: List[float]) -> float:
    dot = sum(x*y for x, y in zip(a, b))
    na = math.sqrt(sum(x*x for x in a)) or 1.0
    nb = math.sqrt(sum(x*x for x in b)) or 1.0
    return dot / (na * nb)

@lru_cache(maxsize=4096)
def _embed_cache(key: str) -> Tuple[float, ...]:
    # LRU cache per text to reduce calls; tuple for hashability
    raise RuntimeError("embed cache should be filled by async wrapper")

async def _embed_texts(texts: List[str]) -> List[List[float]]:
    # text-embedding-3-small is cheap and good for this task
    resp = await client.embeddings.create(model="text-embedding-3-small", input=texts)
    return [d.embedding for d in resp.data]

async def _embed_with_cache(text: str) -> List[float]:
    # Try cache; if missing, compute and backfill via monkey-patch
    try:
        tup = _embed_cache(text)  # type: ignore
        return list(tup)
    except Exception:
        vec = (await _embed_texts([text]))[0]
        # monkey fill the cache
        def _store(k: str, v: Tuple[float, ...]):
            _embed_cache.__wrapped__.cache[k] = v  # type: ignore
        _store(text, tuple(vec))
        return vec

# ========== Main scoring ==========

async def get_similarity_score(guess: str, correct: Dict[str, str]) -> int:
    """
    Returns an int in [0, 1000].
    Hard rules:
      - 1000 only if the SONG TITLE matches (minor typos allowed).
      - Correct artist but wrong/unspecified title => high (≈900–980), but never 1000.
      - Far guesses => low.
    Uses: deterministic checks -> embeddings -> one LLM 'nudge' with strict JSON.
    """
    title_raw = correct.get("title", "") or ""
    artist_raw = correct.get("artist", "") or ""
    guess_raw = guess or ""

    n_title = norm(title_raw)
    n_artist = norm(artist_raw)
    n_both = (n_title + " " + n_artist).strip()
    n_guess = norm(guess_raw)

    # ---------- 1) Deterministic fast paths ----------
    best_exact = 0
    best_title_dist, best_artist_dist = 1.0, 1.0
    saw_artist_exact = False
    saw_title_exact = False

    for g_title, g_artist in _candidate_splits(n_guess):
        td = nlev(g_title, n_title)
        ad = nlev(g_artist, n_artist)
        saw_title_exact |= (td <= 0.08) or (_token_set_ratio(g_title, n_title) >= 0.95)
        saw_artist_exact |= (ad <= 0.08) or (_token_set_ratio(g_artist, n_artist) >= 0.95)

        # Exact song (title) wins everything (artist may be omitted or wrong in user text)
        if td <= 0.08 or (_token_set_ratio(g_title, n_title) >= 0.98):
            # If artist is also very close, it's trivially 1000
            if ad <= 0.12 or g_artist == "" or _token_set_ratio(g_artist, n_artist) >= 0.9:
                return 1000
            best_exact = max(best_exact, 995)  # title exact but artist unclear/wrong

        best_title_dist = min(best_title_dist, td)
        best_artist_dist = min(best_artist_dist, ad)

    # Artist exact, title not exact => strong but < 1000
    if saw_artist_exact and not saw_title_exact:
        # Closer the (wrong) title is, higher we go, but cap < 1000
        boost = int(round(60 * max(0.0, 1.0 - best_title_dist)))  # up to +60
        return max(900, min(980, 900 + boost))

    # ---------- 2) Embeddings-based coarse similarity ----------
    # Compare guess to: "title by artist", artist, title
    combo = f"{title_raw} by {artist_raw}".strip()
    texts = [guess_raw, combo, artist_raw, title_raw]
    gv, cv, av, tv = await _embed_texts(texts)
    sim_combo = _cos(gv, cv)            # strongest signal if they sort of describe the song
    sim_artist = _cos(gv, av)
    sim_title  = _cos(gv, tv)

    # Map embedding similarity (~-1..1) to [0..1] (clip and shift), then curve
    def _sim01(x: float) -> float:
        x = max(-1.0, min(1.0, x))
        return max(0.0, x)  # clip negatives to 0 (we only reward)
    s_combo = _sim01(sim_combo)
    s_artist = _sim01(sim_artist)
    s_title  = _sim01(sim_title)

    # Heuristic base (0..850). Emphasize combo; blend artist/title.
    base_sem = max(s_combo, 0.65 * s_artist + 0.35 * s_title)
    # Slightly convex to push weak sims down
    base_sem_score = int(round(850 * (base_sem ** 1.25)))

    # If both edit-dists are large and sims tiny, don't let base run too high
    if best_title_dist > 0.35 and best_artist_dist > 0.35 and base_sem < 0.12:
        base_sem_score = min(base_sem_score, 180)

    # If our earlier deterministic near-title hit exists, respect it
    base_score = max(best_exact, base_sem_score)

    # ---------- 3) One small LLM 'nudge' for nuanced associations ----------
    # Only call the LLM if we are not already certain (e.g., exact 1000 handled).
    system = (
        "You are a strict song-guess scorer for a daily music game. "
        "Return ONLY compact JSON: "
        '{"match_type":"one of: exact_song, correct_artist, near_miss, similar_artist_or_song, weak_relation, unrelated",'
        '"score":0,"reason":"short"} '
        "Rules: 1000 ONLY for exact song (minor typos OK). Correct artist but wrong/unspecified title: 900–980. "
        "Same song wrong artist: 850–930. Similar artist/era/genre/common-confusion: 700–880. "
        "Some cues (genre/decade/language/mood) but not close: 400–699. Weak relation: 200–399. Unrelated: 0–199."
    )

    user = f"""
Correct:
- title: "{title_raw}"
- artist: "{artist_raw}"

User guess (raw): "{guess_raw}"

Signals:
- best_title_edit_distance_norm: {best_title_dist:.3f}
- best_artist_edit_distance_norm: {best_artist_dist:.3f}
- sim(guess, "title by artist"): {s_combo:.3f}
- sim(guess, artist): {s_artist:.3f}
- sim(guess, title): {s_title:.3f}

Hard constraints you MUST obey:
- Only output 1000 when the *song title* matches (small typos allowed).
- If artist is correct but title is wrong/unspecified, stay in 900–980.
- If both far (edit > 0.35 & sims < 0.12), keep score ≤ 200.

Now score the guess.
"""

    try:
        llm = await client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0,
            top_p=0,
            response_format={"type": "json_object"},
            max_tokens=120,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        obj = json.loads(llm.choices[0].message.content)
        llm_score = int(obj.get("score", 0))
    except Exception:
        llm_score = 0  # fall back gracefully

    # ---------- 4) Post-rules + fuse scores ----------
    fused = int(round(0.6 * base_score + 0.4 * llm_score))

    # Enforce global bounds and golden rules
    # If title is exact (within tight threshold), make it 1000
    if saw_title_exact or best_title_dist <= 0.08:
        fused = 1000

    # If artist is exact but title isn't, clamp 900–980
    if saw_artist_exact and not (saw_title_exact or best_title_dist <= 0.08):
        fused = max(900, min(980, fused))

    # If really far by both heuristics, cap low
    if best_title_dist > 0.35 and best_artist_dist > 0.35 and max(s_combo, s_artist, s_title) < 0.12:
        fused = min(fused, 200)

    return max(0, min(1000, fused))
