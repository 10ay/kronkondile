from re import I
import random
from engine.discover import Discover
from engine.seeds import *
from frontend.recommend import *
from engine.ratings import *
from frontend.scrape_music import *
from engine.graph_expand import *

def open_artist(artist):
    #track = open_artist_top_song(artist)
    track = open_artist_on_lastfm(artist)
   # import pdb; pdb.set_trace()
    print(f"  → {track.title}")
    print(f"Here's a link to this artist's discography!")
    print(f"  → {track.url}")
    return track


def expand_favorites_on_quit(session, quiet):
    result = maybe_expand_graph_on_quit(session.like, quiet)
    if not result:
        return
    if result["expanded"]:
        s = result["stats"]
        print(f"\nGraph updated: {s['artists']} artists, {s['edges']} edges")
    if result["failed"]:
        print(f"Could not expand: {', '.join(result['failed'])}")

def main():
    result = get_feeling()
    if result is None:
        return
    mood_index, mood_label = result
    session = Discover.from_file_with_history(mood_index)

    seeds = seed_by_mood()[mood_index]
    #import pdb; pdb.set_trace()
    
    in_graph = [a for a in seeds if a in session.graph]
    if not in_graph:
        print("No mood seeds found in graph.")
        return
    available = [a for a in in_graph if a not in session.today_seen]
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
    print(f"\nThese are your artists for this mood: {seeds}")
    artist_desired = input(f"\nWhich artist do you want recommendations for?")

    if artist_desired not in seeds:
        print("Cheeky bugger, that artist is not in your mood seeds. I will select a random artist from your mood seeds. ")
        current = random.choice(in_graph)
    else:
        current = artist_desired
    session.seed_artist = current 
    session.seen.add(current)

    print(f"Mood: {mood_label}\n")
    while current:
        print(f"\nArtist: {current}")
        open_artist(current)
        
        choice = input("  [l]ike  [d]islike  [u]nknown  [q]uit: ").strip().lower()
        if choice == "q":
            print("Would you like to see the artists you liked today?")
            see_today = input("Type 'y' for yes, 'n' for no: ").strip().lower()
            if see_today == "y":
                updated_session = Discover.from_file_with_history(mood_index)
                print(f"\nThese are the artists you have liked today: {updated_session.artists_today_liked}")
                print(f"\nThese are the artists you have liked in this session: {session.like}")
                print(f"\n Would you like to add artists from this session to your favorites?")
                add_to_favorites = input("Type 'y' for yes, 'n' for no: ").strip().lower()
                if add_to_favorites == "y":
                    log_all_time_favorites(session.like, mood_index)
                    expand_favorites_on_quit(session, quiet=False)
                # Update seeds with add_to_favorites
            break
        if choice == "l":
            session.rate_artist(current, "like")
            log_rating(current, "like", mood_index)
        elif choice == "d":
            session.rate_artist(current, "dislike")
            log_rating(current, "dislike", mood_index)
        elif choice == "u":
            session.rate_artist(current, "unknown")
            log_rating(current, "unknown", mood_index)            
            
        current = session.next_artist()

        if current is None:
            print("\nNo more recommendations in this session.")
            break

        print(
        f"\nSession: {len(session.like)} likes, "
        f"{len(session.dislike)} dislikes, "
        f"{len(session.seen)-1} artists seen"
    )  




if __name__ == "__main__":
    main()