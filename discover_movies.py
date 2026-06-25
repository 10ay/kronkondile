import random
from engine.movie_discover import Discover
from engine.movie_seeds import *
from recommend import *
from engine.movie_ratings import *
from scrape_movies import *

def open_movie(movie):
    track = open_movie_on_tmdb(movie)
    print(f"  → {track.title}" + (f" ({track.year})" if track.year else ""))
    print(f"Here's a link on TMDB!")
    print(f"  → {track.url}")
    return track

def main():
    result = get_feeling()
    if result is None:
        return
    mood_index, mood_label = result

    try:
        session = Discover.from_file_with_history(mood_index)
    except RuntimeError as exc:
        print(f"Cannot build movie graph: {exc}")
        print("Set TMDB_API_KEY, then run: python movie_graph.py")
        return

    seeds = seed_by_mood()[mood_index]
    in_graph = [m for m in seeds if m in session.graph]
    if not in_graph:
        print("No mood seeds found in graph.")
        return
    available = [m for m in in_graph if m not in session.today_seen]
    if not available:
        print("You've already explored all mood seeds today. Try again tomorrow or another mood.")
        return

    all_time_favorites = session.all_time_favorites
    if all_time_favorites:
        not_in_available = [a for a in all_time_favorites if a not in available and a not in seed_by_mood()[mood_index]]
        if len(not_in_available) <= 5 and len(not_in_available) > 0:
            for i in range(0, len(not_in_available)):
                not_in_available_to_add = not_in_available[i]
                available.append(not_in_available_to_add)
        else:
            random_integer = random.sample(range(0, len(not_in_available)), 5)
            for i in range(0, 5):
                not_in_available_to_add = not_in_available[random_integer[i]]
                available.append(not_in_available_to_add)
    


    seeds = available
    print(f"\nThis is your latest mood: {mood_label}")
    print(f"\nThese are your films for this mood: {seeds}")
    movie_desired = input(f"\nWhich film do you want recommendations for? ")

    if movie_desired not in seeds:
        print("That film is not in your mood seeds. Picking a random one.")
        current = random.choice(in_graph)
    else:
        current = movie_desired

    session.seed_movie = current
    session.seen.add(current)

    print(f"Mood: {mood_label}\n")
    while current:
        print(f"\nFilm: {current}")
        open_movie(current)

        choice = input("  [l]ike  [d]islike  [u]nknown  [q]uit: ").strip().lower()
        if choice == "q":
            print("Would you like to see the films you liked today?")
            see_today = input("Type 'y' for yes, 'n' for no: ").strip().lower()
            if see_today == "y":
                updated_session = Discover.from_file_with_history(mood_index)
                print(f"\nThese are the movies you have liked today: {updated_session.movies_today_liked}")
                print(f"\nThese are the movies you have liked in this session: {session.like}")
                print(f"\n Would you like to add movies from this session to your favorites?")
                add_to_favorites = input("Type 'y' for yes, 'n' for no: ").strip().lower()
                if add_to_favorites == "y":
                    log_all_time_favorites(session.like, mood_index)
            break
        if choice == "l":
            session.rate_movie(current, "like")
            log_rating(current, "like", mood_index)
        elif choice == "d":
            session.rate_movie(current, "dislike")
            log_rating(current, "dislike", mood_index)
        elif choice == "u":
            session.rate_movie(current, "unknown")
            log_rating(current, "unknown", mood_index)

        current = session.next_movie()
        if current is None:
            print("\nNo more recommendations in this session.")
            break
        print(
            f"\nSession: {len(session.like)} likes, "
            f"{len(session.dislike)} dislikes, "
            f"{len(session.seen) - 1} films seen"
        )

if __name__ == "__main__":
    main()
