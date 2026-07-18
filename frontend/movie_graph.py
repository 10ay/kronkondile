"""
Build movie graph: seeds → TMDB → data/movie_graph.json
python movie_graph.py
python movie_graph.py --inspect "Carol"
"""

import argparse
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.movie_seeds import movie_for_each_seed, seed_by_mood
from engine.movie_graph import *
from frontend.recommend import *

def build():
    print("Seed films from movie_library:")
    for mood, movies in seed_by_mood().items():
        print(f"{mood}: {', '.join(movies)}")

    seed_movies = movie_for_each_seed()
    result = get_feeling()
    if result is None:
        print("Why do you have no feelings today?")
        return
    mood_index, mood_label = result

    api_key = get_api()
    try:
        graph = load_graph(default_graph_path)
        out_path = default_graph_path
        print("\nLoaded existing graph (delete data/movie_graph.json to rebuild).")
    except FileNotFoundError:
        print("\nBuilding graph from TMDB (takes a few minutes)...")
        graph = build_graph_from_seeds(seed_movies, api_key)
        out_path = save_graph(graph, default_graph_path)

    stats = graph_statistics(graph)
    print("\nGraph ready.")
    print(f"  file:           {out_path}")
    print(f"  movies:         {stats['movies']}")
    print(f"  edges:          {stats['edges']}")
    print(f"  average_weight: {stats['average_weight']}")

def inspect(movie):
    graph = load_graph(default_graph_path)
    matches = neighbors_of(graph, movie, top_k=15)
    if not matches:
        print(f"No neighbors for {movie!r} — is it in the graph?")
        return
    print(f"Neighbors of {movie!r}:")
    for name, weight in matches:
        print(f"  {name:35} {weight:.2f}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--inspect", metavar="MOVIE", help="Inspect a film in the saved graph")
    args = parser.parse_args()
    if args.inspect:
        inspect(args.inspect)
    else:
        build()

if __name__ == "__main__":
    main()