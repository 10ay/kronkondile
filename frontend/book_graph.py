"""
The book_graph.py is run through here using book_seeds.py and recommend.py.
"""

import argparse
from engine.book_seeds import book_for_each_seed, seed_by_mood
from engine.book_graph import *
from frontend.recommend import *

def build():
    """
    Use seeds -> query open library -> json file
    """
    print("Seed books from book library will be printed below:")


    for mood, books in seed_by_mood().items():
        print(f"{mood}: {', '.join(books)}")
    seed_books = book_for_each_seed()
    
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
    #import pdb; pdb.set_trace()
    
    try:
        graph = load_graph(default_graph_path)
        out_path = default_graph_path
    except FileNotFoundError:
        graph = build_graph_from_seeds(seed_books, api_key)
        out_path = save_graph(graph, default_graph_path)


    stats = graph_statistics(graph)
    print("\nGraph built.")
    print(f"  file:          {out_path}")
    print(f"  books:         {stats['books']}")
    print(f"  edges:         {stats['edges']}")
    print(f"  average_weight: {stats['average_weight']}")

    print(f"\nThis is your latest mood: {mood_label}")
    print(f"\nThese are your books for this mood: {mood_seeds}")
    book_desired = input(f"\nWhich book do you want recommendations for?")

    if book_desired not in seed_books:
        print(f"ERROR: {book_desired} is not in your seed books.")
        return

    else:
        sample = book_desired
        book_index = mood_seeds.index(sample)

    print(f"\nIf you like {book_desired}, you will like: {sample!r}:")

    neighbors = neighbors_of(graph, sample, top_k=15)

    for name, weight in neighbors:
        print(f"  {name:30} {weight:.2f}")

    print(f"\nRead this book by your desired author From Your Mood Map!")
    #import pdb; pdb.set_trace()
    recommendations = get_recommendations_book(rand_int = book_index)
    feeling_index, feeling_name = get_feeling()
    print(format_recommendations(recommendations, feeling_name=feeling_name))

    
    for name, weight in neighbors:
        if name not in seed_books:
            seed_books.append(name)


    print(f"\nI will now expand the graph size. Hold on! Nothing is required of you.")
    graph = build_graph_from_seeds(seed_books, api_key)
    out_path = save_graph(graph, default_graph_path)


def inspect(book):
    """
    Loafd saved graph. like a read-only mode. reads json from disk without api.
    """

    graph = load_graph(default_graph_path)
    matches = neighbors_of(graph, book, top_k=15)

    if not matches:
        print("ERROR")
        return
    
    print(f"Neighbors of {book!r}:")
    for name, weight in matches:
        print(f"  {name:30} {weight:.2f}")

def main():
    """
    Main function.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--inspect", metavar = "BOOK", help = "Inspect a book")
    args = parser.parse_args()

    if args.inspect:
        inspect(args.inspect)
    else:
        build()

if __name__ == "__main__":
    main()
