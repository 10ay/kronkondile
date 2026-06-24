from __future__ import annotations
from datetime import date
from pathlib import Path

root = Path(__file__).resolve().parent.parent
ratings_path = root / "data" / "movie_ratings.tsv"

def log_rating(movie, verdict, mood_index):
    ratings_path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not ratings_path.exists() or ratings_path.stat().st_size == 0
    with ratings_path.open("a", encoding="utf-8") as f:
        if write_header:
            f.write("date\tmovie\tverdict\tmood\n")
        mood = "" if mood_index is None else str(mood_index)
        f.write(f"{date.today()}\t{movie}\t{verdict}\t{mood}\n")

def load_ratings():
    if not ratings_path.exists():
        return []
    rows = []
    lines = ratings_path.read_text(encoding="utf-8").splitlines()
    if not lines:
        return []
    start = 1 if lines[0].startswith("date\t") else 0
    for line in lines[start:]:
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        rows.append({
            "date": parts[0],
            "movie": parts[1],
            "verdict": parts[2],
            "mood": parts[3] if len(parts) > 3 else None,
        })
    return rows

def liked_from_history(mood_index=None):
    likes = set()
    for row in load_ratings():
        if row["verdict"] != "like":
            continue
        if mood_index is not None and row["mood"] != str(mood_index):
            continue
        likes.add(row["movie"])
    return likes

def disliked_from_history(mood_index=None):
    dislikes = set()
    for row in load_ratings():
        if row["verdict"] != "dislike":
            continue
        if mood_index is not None and row["mood"] != str(mood_index):
            continue
        dislikes.add(row["movie"])
    return dislikes

def movies_today(mood_index=None):
    today = str(date.today())
    movies = set()
    for row in load_ratings():
        if row["date"] != today:
            continue
        if mood_index is not None and row["mood"] != str(mood_index):
            continue
        movies.add(row["movie"])
    return movies

def movies_today_liked(mood_index=None):
    today = str(date.today())
    liked = set()
    for row in load_ratings():
        if row["date"] != today:
            continue
        if mood_index is not None and row["mood"] != str(mood_index):
            continue
        if row["verdict"] == "like":
            liked.add(row["movie"])
    return liked