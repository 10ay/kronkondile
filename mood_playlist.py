
"""
Mood playlist
"""

from __future__ import annotations

import html
import webbrowser
from pathlib import Path

from feelings import feelings_dictionary
from recommend import get_feeling
from engine.mood_playlist import *


root = Path(__file__).resolve().parent
template_path = root / "static" / "mood_playlist.html"
out_path = root / "data" / "mood_playlist.html"


def load_template():
    if not template_path.exists():
        raise FileNotFoundError(f"Missing template: {template_path}")
    return template_path.read_text(encoding="utf-8")


def render_playlist_html(tracks, mood_label, meta, out_path):
    cards = []
    for t in tracks:
        cards.append(f"""
<article class="track">
  <div class="art" aria-hidden="true"></div>
  <div class="info">
    <div class="title">{html.escape(t["title"])}</div>
    <div class="artist">{html.escape(t["artist"])}</div>
  </div>
  <div class="actions">
    <a href="{html.escape(t["lastfm_url"])}" target="_blank" rel="noopener">Last.fm</a>
  </div>
</article>""")

    page = load_template()
    page = page.replace("<!--MOOD_LABEL-->", html.escape(mood_label))
    page = page.replace("<!--META-->", html.escape(meta))
    page = page.replace("<!--TRACKS-->", "\n".join(cards))

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(page, encoding="utf-8")
    return out_path


def pick_mood(default_index=None):
    print("\nMood:")
    for i, label in feelings_dictionary.items():
        mark = "  ← today" if default_index is not None and i == default_index else ""
        print(f"  [{i}] {label}{mark}")
    default = default_index if default_index is not None else 3
    raw = input(f"Mood 0-4 [{default}]: ").strip()

    if not raw:
        return default
    
    try:
        mood = int(raw)
    except ValueError:
        return default
    
    return mood if mood in feelings_dictionary else default


def pick_activity():
    print("\nActivity:")
    for i, name in enumerate(activity_list):
        print(f"  [{i}] {name}")
    raw = input("Activity [0=none]: ").strip()
    try:
        idx = int(raw) if raw else 0
    except ValueError:
        idx = 0
    if idx < 0 or idx >= len(activity_list):
        idx = 0
    return activity_list[idx]


def pick_genre():
    print("\nGenre:")
    for i, g in enumerate(genres):
        print(f"  [{i}] {g}")
    raw = input("Genre [0=any]: ").strip()
    try:
        idx = int(raw) if raw else 0
    except ValueError:
        idx = 0
    if idx < 0 or idx >= len(genres):
        idx = 0
    return genres[idx]


def pick_tempo(default="slow"):
    print("\nTempo:")
    print("  [1] slow")
    print("  [2] fast")
    hint = "1" if default == "slow" else "2"
    raw = input(f"Tempo [{hint}={default}]: ").strip()
    if not raw:
        return default
    if raw == "2":
        return "fast"
    if raw == "1":
        return "slow"
    return default


def main():
    print("\n=== Mood Playlist Generator ===")

    
    feeling_index, feeling_name = get_feeling()
    mood = feeling_index

    activity = pick_activity()
    genre = pick_genre()
    tempo_default = acitivity_default_tempo.get(activity, "slow")
    tempo = pick_tempo(default=tempo_default)

    length_raw = input("How many tracks? [20]: ").strip()
    try:
        length = max(5, int(length_raw)) if length_raw else 20
    except ValueError:
        length = 20

    print("\nBuilding playlist...")
    print(f"Mood: {feeling_name}")
    result = generate_mood_playlist(
        mood,
        activity=activity,
        genre=genre,
        tempo=tempo,
        length=length,
    )

    if result.get("error"):
        print(result["error"])
        return
    if not result["artists"]:
        print("No artists found.")
        return

    print(f"Resolving songs for {len(result['artists'])} artists...")
    tracks = [t for t in songs_from_artists(result["artists"]) if t]

    meta = (
        f"{len(tracks)} tracks · activity={result['activity']} · "
        f"genre={result['genre']} · tempo={result['tempo']}"
    )
    path = render_playlist_html(
        tracks,
        mood_label=feelings_dictionary[mood],
        meta=meta,
        out_path=out_path,
    )
    print(f"\nSaved {path}")
    webbrowser.open(path.resolve().as_uri())


if __name__ == "__main__":
    main()
    
    
    