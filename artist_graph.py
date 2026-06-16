"""
The graph.py is run through here using seeds.py and recommend.py.
"""

import argparse
from engine.seeds import artist_for_each_seed, seed_by_mood
from engine.graph import *
from recommend import *

def build():
    """
    Use seeds -> query last.fm -> json file
    """
    print("Seed artists from music library will be printed below:")


    for mood, artists in seed_by_mood().items():
        print(f"{mood}: {', '.join(artists)}")
    seed_artists = artist_for_each_seed()
    
    result = get_feeling()
    if result is None:
        print("Why do you have no feelings today?")
        return
    else:
        mood_index, mood_label = result
    
    mood_seeds = seed_by_mood()[mood_index]

    """
    Build graph from all 25 seeds, not from 5 for each mood. Bigger graph.
    """
    
    api_key = get_api()
    
    if load_graph(default_graph_path) is None:
        graph = build_graph_from_seeds(seed_artists, api_key)
        out_path = save_graph(graph, default_graph_path)
    else:
        graph = load_graph(default_graph_path)
        out_path = default_graph_path


    stats = graph_statistics(graph)
    print("\nGraph built.")
    print(f"  file:          {out_path}")
    print(f"  artists:       {stats['artists']}")
    print(f"  edges:         {stats['edges']}")
    print(f"  average_weight: {stats['average_weight']}")

    print(f"\nThis is your latest mood: {mood_label}")
    print(f"\nThese are your artists for this mood: {mood_seeds}")
    artist_desired = input(f"\nWhich artist do you want recommendations for?")

    if artist_desired not in seed_artists:
        print(f"ERROR: {artist_desired} is not in your seed artists.")
        return

    else:
        sample = artist_desired
        artist_index = mood_seeds.index(sample)

    print(f"\nIf you like {artist_desired}, you will like: {sample!r}:")

    neighbors = neighbors_of(graph, sample, top_k=15)

    for name, weight in neighbors:
        print(f"  {name:30} {weight:.2f}")

    print(f"\nListen to this music by your desired artist From Your Mood Map!")
    import pdb; pdb.set_trace()
    recommendations = get_recommendations(rand_int = artist_index)
    feeling_index, feeling_name = get_feeling()
    print(format_recommendations(recommendations, feeling_name=feeling_name))

    
    for name, weight in neighbors:
        if name not in seed_artists:
            seed_artists.append(name)


    print(f"\nI will now expand the graph size. Hold on! Nothing is required of you.")
    graph = build_graph_from_seeds(seed_artists, api_key)
    out_path = save_graph(graph, default_graph_path)


def inspect(artist):
    """
    Loafd saved graph. like a read-only mode. reads json from disk without api.
    """

    graph = load_graph(default_graph_path)
    matches = neighbors_of(graph, artist, top_k=15)

    if not matches:
        print("ERROR")
        return
    
    print(f"Neighbors of {artist!r}:")
    for name, weight in matches:
        print(f"  {name:30} {weight:.2f}")

def main():
    """
    Main function.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--inspect", metavar = "ARTIST", help = "Inspect an artist")
    args = parser.parse_args()

    if args.inspect:
        inspect(args.inspect)
    else:
        build()

if __name__ == "__main__":
    main()