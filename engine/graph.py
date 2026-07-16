"""
Build an artist graph.
Use Last.fm API to get artist data. 

export LASTFM_API_KEY='073fc1c531e63f5da28a9d0a755c87a0'
python -c "
from engine.graph import get_api, fetch_sim_artists
for name, weight in fetch_sim_artists('Noah Kahan', get_api(), limit=15):
    print(f'{name:30} {weight:.2f}')
"""


from __future__ import annotations
import json, os, time
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus
import requests

Graph = dict[str, dict[str, float]]

root = Path(__file__).resolve().parent.parent
default_graph_path = root / "data" / "artist_graph.json"

lastfm_url = "https://ws.audioscrobbler.com/2.0/"

lastfm_base = "https://www.last.fm"

def lastfm_artist_url(artist: str) -> str:
    return f"{lastfm_base}/music/{quote_plus(artist)}"

def lastfm_track_url(artist: str, track: str) -> str:
    return f"{lastfm_base}/music/{quote_plus(artist)}/_/{quote_plus(track)}"



#LASTFM_API_KEY = "073fc1c531e63f5da28a9d0a755c87a0"

def get_api():
    key = os.environ.get("LASTFM_API_KEY", "").strip()
    if key:
        return key
    key = "073fc1c531e63f5da28a9d0a755c87a0"
    return key

def fetch_sim_artists(artist, api_key, limit):
    timeout_time = 10
    params = {
        "method": "artist.getSimilar",
        "artist": artist,
        "api_key": api_key,
        "format": "json",
        "limit": limit,
    }
    response = requests.get(lastfm_url, params=params, timeout=timeout_time)
    response.raise_for_status()
    payload = response.json()
    raw_similar_artists = payload.get("similarartists", {}).get("artist", [])
    if isinstance(raw_similar_artists, dict):
        raw_similar_artists = [raw_similar_artists]
    
    neighbor_artists: list[tuple[str, float]] = []
    for similar_artist in raw_similar_artists:
        name_of_artist = str(similar_artist.get("name", "")).strip()
        if not name_of_artist:
            continue
        neighbor_artists.append((name_of_artist, float(similar_artist.get("match", 0.0))))
    return neighbor_artists




def fetch_top_track(artist, api_key, limit=1):
    timeout_time = 10
    params = {
        "method": "artist.getTopTracks",
        "artist": artist,
        "api_key": api_key,
        "format": "json",
        "limit": limit,
    }
    response = requests.get(lastfm_url, params=params, timeout=timeout_time)
    response.raise_for_status()
    payload = response.json()
    raw_tracks = payload.get("toptracks", {}).get("track", [])
    if isinstance(raw_tracks, dict):
        raw_tracks = [raw_tracks]
    if not raw_tracks:
        return None
    return str(raw_tracks[0].get("name", "")).strip() or None
    
###############################################################
#Build graphs connecting artists to their similar artists now.#
###############################################################

def ensure_node(graph, artist):
    graph.setdefault(artist, {})

def add_edge(graph, artist_a, artist_b, weight):
    """
    If artist a is close to b, b is close to a.
    Keep the heigher weight if we see the same pair twice
    """
    if artist_a == artist_b or weight <= 0:
        return
    else:
        ensure_node(graph, artist_a)
        ensure_node(graph, artist_b)

    graph[artist_a][artist_b] = max(graph[artist_a].get(artist_b, 0.0), weight)
    graph[artist_b][artist_a] = max(graph[artist_b].get(artist_a, 0.0), weight)

def build_graph_from_seeds(seed_artists, api_key, neighbors_per_seed = 100, pause_seconds = 0.25):
    graph = {}
    for i, seed in enumerate(seed_artists, start = 1):
        ensure_node(graph, seed)
        try:
            neighbors = fetch_sim_artists(seed, api_key, neighbors_per_seed)
        except requests.RequestException:
            continue

        for neigbor, weight in neighbors:
            add_edge(graph, seed, neigbor, weight)

        if pause_seconds>0:
            time.sleep(pause_seconds)
        
    return graph 

def save_graph(graph, path):
    """
    Save the graph to a file
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(graph, indent=2))
    return path

def load_graph(path):
    """
    Load the graph from a file.
    """
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
    edges = sum(len(neighbors) for neighbors in graph.values()) // 2 # Don't repeat edges.
    weights = [w for neighbors in graph.values() for w in neighbors.values()]
    if weights:
        return {
        "artists": len(graph),
        "edges": edges,
        "average_weight": round(sum(weights) / len(weights), 3)
        }
    else:
        return {
        "artists": len(graph),
        "edges": edges,
        "average_weight": 0.0
        }

def neighbors_of(graph, artist, top_k):
    """
    Find closest neighbor to an artist 
    k.
    """
    ranked = sorted(graph.get(artist, {}).items(), key = lambda item: (-item[1], item[0]))
    return ranked[:top_k]





