"""
Flask app for Kronkondile
"""


from __future__ import annotations
import random
import sys
import types
import uuid
from datetime import datetime as dt
from pathlib import Path
import pandas as pd
from flask import Flask, jsonify, request, send_from_directory
import threading




_root = Path(__file__).resolve().parent
fake_feelings = types.ModuleType("feelings")
fake_feelings.FEELINGS_FILE = str(_root / "frontend" / "feelings.txt")

fake_feelings.feelings_dictionary = {
    0 : "Lovesick / I feel unloved, like a kidney stone.",
    1 : "Average / You are that penguin heading towards the mountains, 70 kilometeres away.",
    2 : "Silly / You are going to talk to your dog about homosexuality and communism.",
    3 : "Happy / as happy as a minion around Gru.",
    4 : "I Love Everything! / Life is all rainbows and sunshine."}

sys.modules["feelings"] = fake_feelings


feelings_file = Path(__file__).parent / "frontend" / "feelings.txt"

feelings_dictionary = {    
    0 : "Lovesick / I feel unloved, like a kidney stone.",
    1 : "Average / You are that penguin heading towards the mountains, 70 kilometeres away.",
    2 : "Silly / You are going to talk to your dog about homosexuality and communism.",
    3 : "Happy / as happy as a minion around Gru.",
    4 : "I Love Everything! / Life is all rainbows and sunshine."}

feel_prompt = ('''
===================================================

    How are you feeling, today?  Choose 0-4:
    
    0 : Lovesick / I feel unloved, like a kidney stone.
    1 : Average / You are that penguin heading towards the mountains, 70 kilometeres away.
    2 : Silly / You are going to talk to your dog about homosexuality and communism.
    3 : Happy / as happy as a minion around Gru.
    4 : I Love Everything! / Life is all rainbows and sunshine.

===================================================
    ''').strip("\n")

app = Flask(__name__, static_folder = "static")
music_sessions, book_sessions, movie_sessions = {}, {}, {}

def today_str():
    return dt.strftime(dt.now(), "%d-%b-%Y")


def expand_likes_async(liked):
    def _run():
        from engine.graph_expand import maybe_expand_graph_on_quit
        maybe_expand_graph_on_quit(liked, quiet=True)
    threading.Thread(target=_run, daemon=True).start()


def logged_today():
    if not feelings_file.exists():
        return False
    tail = feelings_file.read_text(encoding="utf-8").strip().splitlines()
    if not tail:
        return False
    last_line = tail[-1]
    if last_line.startswith("feel"):  # header row
        return False
    parts = last_line.split("\t")
    return len(parts) >= 2 and parts[1] == today_str()

def get_feeling():
    """
    Get how you feel today. recommend.get_feeling()
    """
    if not feelings_file.exists():
        print("Why do you have no feelings today?")
        return None
    df = pd.read_csv(feelings_file, sep = '\t', names = ['feeling_scale', 'date'])
    if df.empty:
        print("Why do you have no feelings today?")
        return None
    else:
        feeling_index = int(df.iloc[-1]['feeling_scale'])
        return feeling_index, feelings_dictionary[feeling_index]


def mood_from_request():
    """Web users send mood from browser localStorage, not feelings.txt."""
    data = request.get_json(silent=True) or {}
    mood_index = data.get("mood_index")
    if mood_index is None:
        mood_index = request.args.get("mood_index", type=int)
    if mood_index is None:
        return None
    mood_index = int(mood_index)
    if mood_index not in feelings_dictionary:
        return None
    return mood_index, feelings_dictionary[mood_index]


def log_feeling(feel):
    """Mirrors feelings.py."""
    date = today_str()
    if feelings_file.exists():
        tail = feelings_file.read_text(encoding="utf-8").strip().splitlines()
        if tail and tail[-1].split("\t")[1] == date:
            return False
        df = pd.read_csv(feelings_file, sep="\t")
    else:
        feelings_file.touch()
        df = pd.read_csv(feelings_file, sep="\t", names=["feel", "date"])
    df.loc[len(df)] = [feel, date]
    df.to_csv(feelings_file, sep="\t", index=False)
    return True

def track_to_dict(track):
    return {
        "title": getattr(track, "title", None),
        "artist": getattr(track, "artist", None),
        "url": getattr(track, "url", None),
        "channel": getattr(track, "channel", None),
    }


def book_to_dict(book):
    return {
        "title": book.get("title"),
        "author": book.get("author"),
        "url": book.get("url"),
    }

def book_info(title):
    from frontend.scrape_books import book_from_library
    from engine.book_graph import goodreads_book_url
    entry = book_from_library(title)
    if entry:
        return {"title": entry["title"], "author": entry.get("author"), "url": entry["url"]}
    return {"title": title, "author": None, "url": goodreads_book_url(title)}

def book_available_seeds(session, mood_index):
    """Same logic as discover_books.py main()."""
    from engine.book_seeds import seed_by_mood
    seeds = seed_by_mood()[mood_index]
    in_graph = [b for b in seeds if b in session.graph]
    available = [b for b in in_graph if b not in session.today_seen]
    return available, in_graph


def movie_to_dict(movie):
    return {
        "title": movie.get("title"),
        "year": movie.get("year"),
        "url": movie.get("url"),
    }

def movie_info(title):
    from frontend.scrape_movies import movie_from_library
    from engine.movie_graph import tmdb_search_url
    entry = movie_from_library(title)
    if entry:
        return {"title": entry["title"], "year": entry.get("year"), "url": entry["url"]}
    return {"title": title, "year": None, "url": tmdb_search_url(title)}

def movie_available_seeds(session, mood_index):
    """Same logic as discover_movies.py main()."""
    from engine.movie_seeds import seed_by_mood
    seeds = seed_by_mood()[mood_index]
    in_graph = [m for m in seeds if m in session.graph]
    available = [m for m in in_graph if m not in session.today_seen]
    favorites = session.all_time_favorites

    if favorites:
        not_in_available = [
            m for m in favorites
            if m not in available and m not in seed_by_mood()[mood_index]
        ]
        if 0 < len(not_in_available) <= 5:
            available.extend(not_in_available)
        elif len(not_in_available) > 5:
            picks = random.sample(range(len(not_in_available)), 5)
            available.extend(not_in_available[i] for i in picks)

    return available, in_graph


def movie_discover_session(mood_index):
    from engine.movie_discover import Discover
    return Discover.from_file_with_history(mood_index)

def music_available_seeds(session, mood_index):
    """Same as discover.music_available_seeds() but no webbrowser.open."""
    from engine.seeds import seed_by_mood
    seeds = seed_by_mood()[mood_index]
    in_graph = [a for a in seeds if a in session.graph]
    available = [a for a in in_graph if a not in session.today_seen]
    all_time_favorites = session.all_time_favorites

    if all_time_favorites:
        not_in_available = [a for a in all_time_favorites if a not in available and a not in seed_by_mood()[mood_index]]

        if 0 < len(not_in_available) <= 5:
            available.extend(not_in_available)
        elif len(not_in_available) > 5:
            picks = random.sample(range(len(not_in_available)), 5)
            available.extend(not_in_available[i] for i in picks)

    return available, in_graph


def music_artist_info(artist):
    from frontend.scrape_music import Tracks
    """Like discover.open_artist() but no webbrowser.open."""
    from engine.graph import lastfm_artist_url
    url = lastfm_artist_url(artist)
    return Tracks(title=artist, artist=artist, url=url, channel="Last.fm")

# A decorator sits above a function and registers that function as the handler for a URL.
# @app.get("/") is a decorator that registers the index function as the handler for the root URL.
#@app.get only reads and does not change the state of the server.
#@app.post sends data to the server.

@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")

@app.get("/api/feeling/prompt")
def api_feeling_prompt():
    return jsonify({
        "ok": True,
        "prompt": feel_prompt,
    })


@app.get("/api/feeling")
def api_get_feeling():
    result = get_feeling()
    if result is None:
        return jsonify({"ok": False, "error": "Why do you have no feelings today?"}), 404
    idx, label = result
    return jsonify({"ok": True, "mood_index": idx, "mood_label": label})


@app.post("/api/feeling")
def api_log_feeling():
    feel = int(request.get_json(force=True)["feel"])
    if feel not in feelings_dictionary:
        return jsonify({"ok": False, "error": "Choose 0-4"}), 400
    log_feeling(feel)
    return jsonify({"ok": True, "mood_index": feel, "mood_label": feelings_dictionary[feel]})


@app.post("/api/quick/music")
def api_quick_music():
    result = mood_from_request()
    if result is None:
        return jsonify({"ok": False, "error": "No mood sent from browser"}), 400
    mood_index, mood_label = result
    from frontend.music_library import mood_music_map
    song = mood_music_map[mood_index][random.randint(0, len(mood_music_map[mood_index]) - 1)]
    return jsonify({
        "ok": True,
        "mood_label": mood_label,
        "title": song["title"],
        "artist": song.get("artist"),
        "url": song["url"],
    })

@app.get("/api/discover/music/seeds")
def api_music_seeds():
    from engine.discover import Discover
    result = mood_from_request()
    if result is None:
        return jsonify({"ok": False, "error": "No mood sent from browser"}), 400
    mood_index, mood_label = result
    session = Discover.from_file_with_history(mood_index)
    available, in_graph = music_available_seeds(session, mood_index)
    if not in_graph:
        return jsonify({"ok": False, "error": "No mood seeds found in graph."}), 400
    if not available:
        return jsonify({"ok": False, "error": "You've already explored all mood seeds today."}), 400
    return jsonify({"ok": True, "mood_label": mood_label, "seeds": available})

@app.post("/api/discover/music/start")
def api_music_start():
    from engine.discover import Discover
    result = mood_from_request()
    if result is None:
        return jsonify({"ok": False, "error": "No mood sent from browser"}), 400
    mood_index, mood_label = result
    data = request.get_json(force=True)
    seed_artist = data.get("seed_artist")
    session = Discover.from_file_with_history(mood_index)
    available, in_graph = music_available_seeds(session, mood_index)
    if not in_graph:
        return jsonify({"ok": False, "error": "No mood seeds found in graph."}), 400
    if not available:
        return jsonify({"ok": False, "error": "All mood seeds seen today."}), 400
    if not seed_artist or seed_artist not in available:
        seed_artist = random.choice(in_graph)
    session.seed_artist = seed_artist
    session.seen.add(seed_artist)
    sid = str(uuid.uuid4())
    music_sessions[sid] = {"session": session, "mood_index": mood_index}
    track = music_artist_info(seed_artist)
    return jsonify({
        "ok": True,
        "session_id": sid,
        "mood_label": mood_label,
        "seeds": available,
        "current": seed_artist,
        "track": track_to_dict(track),
    })

@app.post("/api/discover/music/step")
def api_music_step():
    from engine.discover import Discover
    from engine.ratings import log_rating, log_all_time_favorites
    data = request.get_json(force=True)
    sid = data["session_id"]
    choice = data["choice"]
    current = data["current"]
    add_favorites = data.get("add_favorites", False)
    if sid not in music_sessions:
        return jsonify({"ok": False, "error": "Session expired"}), 404
    bundle = music_sessions[sid]
    session = bundle["session"]
    mood_index = bundle["mood_index"]
    if choice == "q":
        from engine.ratings import artists_today_liked
        payload = {
            "ok": True,
            "done": True,
            "likes_today": list(artists_today_liked(mood_index)),
            "likes_session": list(session.like),
        }
        
        if add_favorites:
            log_all_time_favorites(session.like, mood_index)
            if session.like:
                expand_likes_async(list(session.like))
        del music_sessions[sid]
        return jsonify(payload)
    if choice == "l":
        session.rate_artist(current, "like")
        log_rating(current, "like", mood_index)
    elif choice == "d":
        session.rate_artist(current, "dislike")
        log_rating(current, "dislike", mood_index)
    elif choice == "u":
        session.rate_artist(current, "unknown")
        log_rating(current, "unknown", mood_index)
    nxt = session.next_artist()
    if nxt is None:
        del music_sessions[sid]
        return jsonify({
            "ok": True,
            "done": True,
            "message": "No more recommendations.",
            "likes_session": list(session.like),
        })
    track = music_artist_info(nxt)
    return jsonify({
        "ok": True,
        "done": False,
        "current": nxt,
        "track": track_to_dict(track),
        "stats": {
            "likes": len(session.like),
            "dislikes": len(session.dislike),
            "seen": len(session.seen) - 1,
        },
    })
@app.get("/api/discover/book/seeds")
def api_book_seeds():
    from engine.book_discover import Discover
    result = mood_from_request()
    if result is None:
        return jsonify({"ok": False, "error": "No mood sent from browser"}), 400
    mood_index, mood_label = result
    session = Discover.from_file_with_history(mood_index)
    available, in_graph = book_available_seeds(session, mood_index)
    if not in_graph:
        return jsonify({"ok": False, "error": "No mood seeds found in graph."}), 400
    if not available:
        return jsonify({"ok": False, "error": "You've already explored all mood seeds today."}), 400
    return jsonify({"ok": True, "mood_label": mood_label, "seeds": available})

@app.post("/api/discover/book/start")
def api_book_start():
    from engine.book_discover import Discover
    result = mood_from_request()
    if result is None:
        return jsonify({"ok": False, "error": "No mood sent from browser"}), 400
    mood_index, mood_label = result
    data = request.get_json(force=True)
    seed_book = data.get("seed_book")
    session = Discover.from_file_with_history(mood_index)
    available, in_graph = book_available_seeds(session, mood_index)
    if not in_graph:
        return jsonify({"ok": False, "error": "No mood seeds found in graph."}), 400
    if not available:
        return jsonify({"ok": False, "error": "All mood seeds seen today."}), 400
    if not seed_book or seed_book not in available:
        seed_book = random.choice(in_graph)
    session.seed_book = seed_book
    session.seen.add(seed_book)
    sid = str(uuid.uuid4())
    book_sessions[sid] = {"session": session, "mood_index": mood_index}
    book = book_info(seed_book)
    return jsonify({
        "ok": True,
        "session_id": sid,
        "mood_label": mood_label,
        "seeds": available,
        "current": seed_book,
        "book": book_to_dict(book),
    })

@app.post("/api/discover/book/step")
def api_book_step():
    from engine.book_discover import Discover
    from engine.book_ratings import log_rating, books_today_liked
    data = request.get_json(force=True)
    sid = data["session_id"]
    choice = data["choice"]
    current = data["current"]
    if sid not in book_sessions:
        return jsonify({"ok": False, "error": "Session expired"}), 404
    bundle = book_sessions[sid]
    session = bundle["session"]
    mood_index = bundle["mood_index"]
    if choice == "q":
        payload = {
            "ok": True,
            "done": True,
            "likes_today": list(books_today_liked(mood_index)),
            "likes_session": list(session.like),
        }
        del book_sessions[sid]
        return jsonify(payload)
    if choice == "l":
        session.rate_book(current, "like")
        log_rating(current, "like", mood_index)
    elif choice == "d":
        session.rate_book(current, "dislike")
        log_rating(current, "dislike", mood_index)
    elif choice == "u":
        session.rate_book(current, "unknown")
        log_rating(current, "unknown", mood_index)
    nxt = session.next_book()
    if nxt is None:
        del book_sessions[sid]
        return jsonify({
            "ok": True,
            "done": True,
            "message": "No more recommendations.",
            "likes_session": list(session.like),
        })
    book = book_info(nxt)
    return jsonify({
        "ok": True,
        "done": False,
        "current": nxt,
        "book": book_to_dict(book),
        "stats": {
            "likes": len(session.like),
            "dislikes": len(session.dislike),
            "seen": len(session.seen) - 1,
        },
    })

@app.get("/api/discover/movie/seeds")
def api_movie_seeds():
    result = mood_from_request()
    if result is None:
        return jsonify({"ok": False, "error": "No mood sent from browser"}), 400
    mood_index, mood_label = result
    try:
        session = movie_discover_session(mood_index)
    except RuntimeError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500
    available, in_graph = movie_available_seeds(session, mood_index)
    if not in_graph:
        return jsonify({"ok": False, "error": "No mood seeds found in graph."}), 400
    if not available:
        return jsonify({"ok": False, "error": "You've already explored all mood seeds today."}), 400
    return jsonify({"ok": True, "mood_label": mood_label, "seeds": available})

@app.post("/api/discover/movie/start")
def api_movie_start():
    result = mood_from_request()
    if result is None:
        return jsonify({"ok": False, "error": "No mood sent from browser"}), 400
    mood_index, mood_label = result
    data = request.get_json(force=True)
    seed_movie = data.get("seed_movie")
    try:
        session = movie_discover_session(mood_index)
    except RuntimeError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500
    available, in_graph = movie_available_seeds(session, mood_index)
    if not in_graph:
        return jsonify({"ok": False, "error": "No mood seeds found in graph."}), 400
    if not available:
        return jsonify({"ok": False, "error": "All mood seeds seen today."}), 400
    if not seed_movie or seed_movie not in available:
        seed_movie = random.choice(in_graph)
    session.seed_movie = seed_movie
    session.seen.add(seed_movie)
    sid = str(uuid.uuid4())
    movie_sessions[sid] = {"session": session, "mood_index": mood_index}
    movie = movie_info(seed_movie)
    return jsonify({
        "ok": True,
        "session_id": sid,
        "mood_label": mood_label,
        "seeds": available,
        "current": seed_movie,
        "movie": movie_to_dict(movie),
    })

@app.post("/api/discover/movie/step")
def api_movie_step():
    from engine.movie_ratings import log_rating, log_all_time_favorites, movies_today_liked
    data = request.get_json(force=True)
    sid = data["session_id"]
    choice = data["choice"]
    current = data["current"]
    add_favorites = data.get("add_favorites", False)
    if sid not in movie_sessions:
        return jsonify({"ok": False, "error": "Session expired"}), 404
    bundle = movie_sessions[sid]
    session = bundle["session"]
    mood_index = bundle["mood_index"]
    if choice == "q":
        payload = {
            "ok": True,
            "done": True,
            "likes_today": list(movies_today_liked(mood_index)),
            "likes_session": list(session.like),
        }
        if add_favorites:
            log_all_time_favorites(session.like, mood_index)
        del movie_sessions[sid]
        return jsonify(payload)
    if choice == "l":
        session.rate_movie(current, "like")
        log_rating(current, "like", mood_index)
    elif choice == "d":
        session.rate_movie(current, "dislike")
        log_rating(current, "dislike", mood_index)
    elif choice == "u":
        session.rate_movie(current, "unknown")
        log_rating(current, "unknown", mood_index)
    nxt = session.next_movie()
    if nxt is None:
        del movie_sessions[sid]
        return jsonify({
            "ok": True,
            "done": True,
            "message": "No more recommendations.",
            "likes_session": list(session.like),
        })
    movie = movie_info(nxt)
    return jsonify({
        "ok": True,
        "done": False,
        "current": nxt,
        "movie": movie_to_dict(movie),
        "stats": {
            "likes": len(session.like),
            "dislikes": len(session.dislike),
            "seen": len(session.seen) - 1,
        },
    })


@app.get("/api/mood-playlist/options")
def api_mood_playlist_options():
    from engine.mood_playlist import activity_list, acitivity_default_tempo, genres
    return jsonify({
        "ok": True,
        "activities": activity_list,
        "genres": genres,
        "tempo_defaults": acitivity_default_tempo,
        "tempos": ["slow", "fast"],
    })


@app.post("/api/mood-playlist/generate")
def api_mood_playlist_generate():
    from engine.mood_playlist import generate_mood_playlist, songs_from_artists
    mood = mood_from_request()
    if mood is None:
        return jsonify({"ok": False, "error": "mood_index required (0-4)"}), 400
    mood_index, mood_label = mood

    data = request.get_json(force=True) or {}
    activity = data.get("activity", "Focus")
    genre = data.get("genre", "any")
    tempo = data.get("tempo", "slow")
    try:
        length = int(data.get("length", 20))
    except (TypeError, ValueError):
        length = 20
    length = max(5, min(length, 40))

    result = generate_mood_playlist(
        mood_index,
        activity=activity,
        genre=genre,
        tempo=tempo,
        length=length,
    )
    if result.get("error"):
        return jsonify({"ok": False, "error": result["error"]}), 400
    if not result["artists"]:
        return jsonify({"ok": False, "error": "No artists found for this mood."}), 400

    tracks = [t for t in songs_from_artists(result["artists"]) if t]
    return jsonify({
        "ok": True,
        "mood_index": mood_index,
        "mood_label": mood_label,
        "activity": result["activity"],
        "genre": result["genre"],
        "tempo": result["tempo"],
        "tracks": tracks,
    })


if __name__ == "__main__":
    app.run(debug=True, port=5001)
