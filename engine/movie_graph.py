"""
Build a movie graph.
Use TMDB

export TMDB_API_KEY="your-key"
python -c "
from engine.movie_graph import get_api, fetch_sim_movies
for name, w in fetch_sim_movies('Call Me by Your Name', get_api(), 10):
    print(f'{name:35} {w:.2f}')
"
"""


from __future__ import annotations
import json, os, re, time
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus
import requests

Graph = dict[str, dict[str, float]]

root = Path(__file__).resolve().parent.parent
default_graph_path = root / "data" / "movie_graph.json"
tmdb_base = "https://api.themoviedb.org/3"

def tmdb_search_url(title):
    return f"https://www.themoviedb.org/search/movie?query={quote_plus(title)}"


def get_api():
    key = os.environ.get("TMDB_API_KEY", "").strip()
    if not key:
        raise RuntimeError("Set TMDB_API_KEY (themoviedb.org/settings/api)")
    return key

def cache_path():
    return root / "data" / "tmdb_cache.json"

def cache_key(text):
    return text.strip().lower()

def load_cache():
    path = cache_path()
    if path.exists():
        return json.loads(path.read_text())
    return {}

def save_cache(cache):
    path = cache_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cache, indent=2))

def year_for_movie(title):
    from movie_library import mood_movie_map
    target = title.strip().lower()
    for movies in mood_movie_map.values():
        for entry in movies:
            if entry.get("title", "").strip().lower() == target:
                return entry.get("year")
    return None
            

def normalize_title(title):
    return re.sub(r"\s+", " ", title.strip().lower())


def tmdb_get(api_key, path, params=None):
    """One GET to TMDB. path is like '/search/movie'"""
    params = dict(params or {})
    params["api_key"] = api_key
    response = requests.get(f"{tmdb_base}{path}", params=params, timeout=20)
    response.raise_for_status()
    return response.json()


def search_movie(title, api_key, year = None):
    params = {"query": title}
    if year:
        params["year"] = int(year)
    payload = tmdb_get(api_key, "/search/movie", params)
    results = payload.get("results", [])
    if not results:
        return None
    target = normalize_title(title)
    for movie in results:
        if normalize_title(str(movie.get("title", ""))) == target:
            return movie
    return results[0]

def similar_from_tmdb(movie_id, api_key, limit = 10):
    seen_ids = set()
    neighbors = []

    for endpoint in ("/similar", "/recommendations"):
        payload = tmdb_get(api_key, f"/movie/{movie_id}{endpoint}", {"page": 1})
        for movie in payload.get("results") or []:
            mid = movie.get("id")
            if not mid or mid in seen_ids:
                continue
            seen_ids.add(mid)
            title = str(movie.get("title", "")).strip()
            if not title:
                continue
            # vote_average is 0-10; turn into 0-1 weight
            vote = float(movie.get("vote_average") or 0.0)
            weight = min(vote / 10.0, 1.0) if vote > 0 else 0.5
            neighbors.append((title, weight))
            if len(neighbors) >= limit:
                return neighbors
        time.sleep(0.15)
    return neighbors[:limit]

def fetch_sim_movies(title, api_key, limit):
    """
    Like fetch_sim_artists: given a seed title, return similar films.
    Uses cache so rebuilds are fast and cheap.
    """
    year = year_for_movie(title)
    cache = load_cache()
    entry_key = f"{cache_key(title)}|{cache_key(str(year or ''))}"
    if entry_key in cache:
        return [(t, float(w)) for t, w in cache[entry_key][:limit]]
    found = search_movie(title, api_key, year=year)
    if not found:
        return []
    movie_id = found.get("id")
    if not movie_id:
        return []
    seed_key = cache_key(title)
    neighbors = []
    for name, weight in similar_from_tmdb(movie_id, api_key, limit + 5):
        if cache_key(name) == seed_key:
            continue
        neighbors.append((name, weight))
    neighbors = neighbors[:limit]
    cache[entry_key] = [[t, w] for t, w in neighbors]
    save_cache(cache)
    return neighbors
# --- graph helpers (same pattern as music/books) ---
def ensure_node(graph, movie):
    graph.setdefault(movie, {})
def add_edge(graph, movie_a, movie_b, weight):
    if movie_a == movie_b or weight <= 0:
        return
    ensure_node(graph, movie_a)
    ensure_node(graph, movie_b)
    graph[movie_a][movie_b] = max(graph[movie_a].get(movie_b, 0.0), weight)
    graph[movie_b][movie_a] = max(graph[movie_b].get(movie_a, 0.0), weight)
def build_graph_from_seeds(seed_movies, api_key, neighbors_per_seed=20, pause_seconds=0.25):
    graph = {}
    for seed in seed_movies:
        ensure_node(graph, seed)
        try:
            neighbors = fetch_sim_movies(seed, api_key, neighbors_per_seed)
        except requests.RequestException:
            continue
        for neighbor, weight in neighbors:
            add_edge(graph, seed, neighbor, weight)
        if pause_seconds > 0:
            time.sleep(pause_seconds)
    return graph
def save_graph(graph, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(graph, indent=2))
    return path
def load_graph(path):
    if not path.exists():
        raise FileNotFoundError()
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        raise FileNotFoundError()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        raise FileNotFoundError()
def graph_statistics(graph):
    edges = sum(len(neighbors) for neighbors in graph.values()) // 2
    weights = [w for neighbors in graph.values() for w in neighbors.values()]
    if weights:
        return {
            "movies": len(graph),
            "edges": edges,
            "average_weight": round(sum(weights) / len(weights), 3),
        }
    return {"movies": len(graph), "edges": edges, "average_weight": 0.0}
def neighbors_of(graph, movie, top_k):
    ranked = sorted(graph.get(movie, {}).items(), key=lambda item: (-item[1], item[0]))
    return ranked[:top_k]

def ensure_movie_graph(path=default_graph_path, api_key=None):
    """Load movie_graph.json, or build it from TMDB on first use."""
    try:
        return load_graph(path)
    except FileNotFoundError:
        from engine.movie_seeds import movie_for_each_seed
        print("\nNo data/movie_graph.json yet — building from TMDB (one-time, a few minutes)...")
        key = api_key or get_api()
        graph = build_graph_from_seeds(movie_for_each_seed(), key)
        save_graph(graph, path)
        stats = graph_statistics(graph)
        print(f"Saved {path} ({stats['movies']} movies, {stats['edges']} edges)\n")
        return graph