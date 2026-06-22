from __future__ import annotations
from datetime import date
from pathlib import Path

root = Path(__file__).resolve().parent.parent
ratings_path = root / "data" / "ratings.tsv"
all_time_favorites_path = root / "data" / "all_time_favorites.tsv"


def log_rating(artist, verdict, mood_index):
    ratings_path.parent.mkdir(parents = True, exist_ok = True)
    with ratings_path.open("a", encoding = "utf-8") as f:
        if not ratings_path.exists():
            f.write("date\tartist\tverdict\tmood\n")
        mood = "" if mood_index is None else str(mood_index)
        f.write(f"{date.today()}\t{artist}\t{verdict}\t{mood}\n")

def load_ratings():
    if not ratings_path.exists():
        return []

    rows: list[dict] = []
    lines = ratings_path.read_text(encoding = "utf-8").splitlines()

    if not lines:
        return []

    start = 1 if lines[0].startswith("data\t") else 0
    for line in lines[start:]:
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        date = parts[0]
        artist = parts[1]
        verdict = parts[2]
        mood = parts[3] if len(parts) > 3 else None
        rows.append({
            "date": date,
            "artist": artist,
            "verdict": verdict,
            "mood": mood
        })

    return rows

def load_all_time_favorites():
    if not all_time_favorites_path.exists():
        return []

    rows: list[dict] = []
    lines = all_time_favorites_path.read_text(encoding="utf-8").splitlines()

    if not lines:
        return []

    start = 1 if lines[0].startswith("date\t") else 0
    for line in lines[start:]:
        parts = line.split("\t")
        if len(parts) >= 3:
            row_date = parts[0]
            artist = parts[1]
            mood = parts[2]
        elif len(parts) == 2:
            row_date = ""
            artist = parts[0]
            mood = parts[1]
        elif len(parts) == 1 and parts[0].strip():
            row_date = ""
            artist = parts[0].strip()
            mood = None
        else:
            continue
        rows.append({
            "date": row_date,
            "artist": artist,
            "mood": mood,
        })

    return rows

def log_all_time_favorites(artists, mood_index):
    all_time_favorites_path.parent.mkdir(parents=True, exist_ok=True)
    mood = "" if mood_index is None else str(mood_index)

    existing = {row["artist"] for row in load_all_time_favorites()}
    write_header = (
        not all_time_favorites_path.exists()
        or all_time_favorites_path.stat().st_size == 0
    )

    with all_time_favorites_path.open("a", encoding="utf-8") as f:
        for artist in artists:
            if artist in existing:
                continue
            f.write(f"{date.today()}\t{artist}\t{mood}\n")
            existing.add(artist)

def liked_from_history(mood_index = None):
    likes = set()
    for row in load_ratings():
        if row["verdict"] != "like":
            continue
        if mood_index is not None and row["mood"] != str(mood_index):
            continue
        likes.add(row["artist"])
    return likes

def disliked_from_history(mood_index = None):
    dislikes = set()
    for row in load_ratings():
        if row["verdict"] != "dislike":
            continue
        if mood_index is not None and row["mood"] != str(mood_index):
            continue
        dislikes.add(row["artist"])
    return dislikes

def artists_today(mood_index=None):
    today = str(date.today())
    artists = set()
    for row in load_ratings():
        if row["date"] != today:
            continue
        if mood_index is not None and row["mood"] != str(mood_index):
            continue
        artists.add(row["artist"])
    return artists

def artists_today_liked(mood_index=None):
    today = str(date.today())
    artists_liked = set()
    for row in load_ratings():
        if row["date"] != today:
            continue
        if mood_index is not None and row["mood"] != str(mood_index):
            continue
        if row["verdict"] == "like":
            artists_liked.add(row["artist"])
    return artists_liked

def all_time_favorites(mood_index=None):
    artists_favorite = set()
    for row in load_all_time_favorites():
        if mood_index is not None and row["mood"] != str(mood_index):
            continue
        artists_favorite.add(row["artist"])
    return artists_favorite
