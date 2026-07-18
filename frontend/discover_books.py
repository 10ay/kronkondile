from engine.book_discover import Discover
from engine.book_seeds import *
from frontend.recommend import *
from engine.book_ratings import *
from frontend.scrape_books import *

def open_book(book):
    track = open_book_on_goodreads(book)
   # import pdb; pdb.set_trace()
    print(f"  → {track.title}")
    print(f"Here's a link to this book on Goodreads!")
    print(f"  → {track.url}")
    return track


def main():
    result = get_feeling()
    if result is None:
        return
    mood_index, mood_label = result
    session = Discover.from_file_with_history(mood_index)

    seeds = seed_by_mood()[mood_index]
    #import pdb; pdb.set_trace()
    
    in_graph = [b for b in seeds if b in session.graph]
    if not in_graph:
        print("No mood seeds found in graph.")
        return
    available = [b for b in in_graph if b not in session.today_seen]
    if not available:
        print("You've already explored all mood seeds today. Try again tomorrow or another mood.")
        return
    
    seeds = available
    print(f"\nThis is your latest mood: {mood_label}")
    print(f"\nThese are your books for this mood: {seeds}")
    book_desired = input(f"\nWhich book do you want recommendations for?")

    if book_desired not in seeds:
        print("Cheeky bugger, that book is not in your mood seeds. I will select a random book from your mood seeds. ")
        current = random.choice(in_graph)
    else:
        current = book_desired
    session.seed_book = current 
    session.seen.add(current)

    print(f"Mood: {mood_label}\n")
    while current:
        print(f"\nBook: {current}")
        open_book(current)

        choice = input("  [l]ike  [d]islike  [u]nknown  [q]uit: ").strip().lower()
        if choice == "q":
            print("Would you like to see the books you liked today?")
            see_today = input("Type 'y' for yes, 'n' for no: ").strip().lower()
            if see_today == "y":
                updated_session = Discover.from_file_with_history(mood_index)
                print(f"\nThese are the books you have liked today: {updated_session.books_today_liked}")
            break
        if choice == "l":
            session.rate_book(current, "like")
            log_rating(current, "like", mood_index)
        elif choice == "d":
            session.rate_book(current, "dislike")
            log_rating(current, "dislike", mood_index)
        elif choice == "u":
            session.rate_book(current, "unknown")
            log_rating(current, "unknown", mood_index)            
            
        current = session.next_book()

        if current is None:
            print("\nNo more recommendations in this session.")
            break
        print(
        f"\nSession: {len(session.like)} likes, "
        f"{len(session.dislike)} dislikes, "
        f"{len(session.seen)-1} books seen"
    )  




if __name__ == "__main__":
    main()
