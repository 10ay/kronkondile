"""
Expand graph
"""

from __future__ import annotations
from pathlib import Path 
from engine.graph import *


def expand_graph(artists, path = default_graph_path,  neighbors_per_artist = 40, pause_seconds = 0.25, minimum_skip = 20):
    """
    For an artist, skip if it has minimum skip.
    Otherwiase, fetch from Last.fm and merge into graph
    """
    names = []
    seen = set()
    for artist in artists:
        name = str(artist).strip()
        if name and name not in seen:
            seen.add(name)
            names.append(name)

    if not names: 
        return None
    
    api_key = get_api()
    
    try:
        graph = load_graph(path)
    except FileNotFoundError:
        graph = {}
    
    expanded, skipped, failed = [], [], []

    for i, artist in enumerate(names, start = 1):
        if len(graph.get(artist, {})) >= minimum_skip:
            skipped.append(artist)
            continue
        try:
            neighbors = fetch_sim_artists(artist, api_key, neighbors_per_artist)
        except requests.RequestException:
            failed.append(artist)
            continue
        ensure_node(graph, artist)
        
        for neighbor, weight in neighbors:
            add_edge(graph, artist, neighbor, weight)
        expanded.append(artist)
        print(f"  [{i}/{len(names)}] expanded {artist!r} (+{len(neighbors)} neighbors)")
        if pause_seconds > 0:
            time.sleep(pause_seconds)
    if expanded:
        save_graph(graph, path)
    
    stats = graph_statistics(graph) if graph else None
    return {
        "expanded": expanded,
        "skipped": skipped,
        "failed": failed,
        "stats": stats,
    }


def maybe_expand_graph_on_quit(liked_artists, quiet):
    """
    Safe wrapper: no API key, or nothing to do.
    """
    liked = list(liked_artists or [])
    if not liked:
        return None
    try:
        if not quiet:
            print(f"\nExpanding artist graph for {len(liked)} liked artist(s)...")
        return expand_graph(liked)
    except RuntimeError:
        if not quiet:
            print("Skipping graph expand (LASTFM_API_KEY not set).")
        return None



    return
