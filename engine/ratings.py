from __future__ import annotations
from datetime import date
from pathlib import Path

root = Path(__file__).resolve().parent.parent
ratings_path = root / "data" / "ratings.tsv"


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