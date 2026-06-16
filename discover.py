from unittest import skip
from engine.discover import Discover
from engine.seeds import *
from recommend import *

def main():
    session = Discover.from_file()
    result = get_feeling()
    if result is None:
        return
    mood_index, mood_label = result
    seeds = seed_by_mood()[mood_index]
    import pdb; pdb.set_trace()
    in_graph = [a for a in seeds if a in session.graph]
    if not in_graph:
        print("No mood seeds found in graph.")
        return
    
    print(f"\nThis is your latest mood: {mood_label}")
    print(f"\nThese are your artists for this mood: {seeds}")
    artist_desired = input(f"\nWhich artist do you want recommendations for?")

    if artist_desired not in seeds:
        print("Cheeky bugger, that artist is not in your mood seeds. I will select a random artist from your mood seeds. ")
        current = artist_desired
    else:
        current = artist_desired
    session.seen.add(current)

    print(f"Mood: {mood_label}\n")
    while current:
        print(f"\nArtist: {current}")
        choice = input("  [l]ike  [d]islike  [u]nknown  [q]uit: ").strip().lower()
        if choice == "q":
            break
        if choice == "l":
            session.rate_artist(current, "like")
        elif choice == "d":
            session.rate_artist(current, "dislike")
        elif choice == "u":
            session.rate_artist(current, "unknown")
        else:
            continue
        current = session.next_artist()
        if current is None:
            print("\nNo more recommendations in this session.")
            break


if __name__ == "__main__":
    main()