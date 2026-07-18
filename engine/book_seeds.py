from frontend.book_library import mood_book_map

def pull_book(books):
    """Pull a book. Unique book """
    seen = set()
    titles = []
    for book in books:
        book_name = book["title"]
        if book_name and book_name not in seen:
            seen.add(book_name)
            titles.append(book_name)
    return titles

def seed_by_mood():
    """
    Map mood to book
    """
    return {mood: pull_book(playlist) for mood, playlist in mood_book_map.items()}


def book_for_each_seed():
    """
    Flatten the 25 books.
    """
    seen = set()
    output = []
    for books in seed_by_mood().values():
        for book in books:
            if book not in seen:
                seen.add(book)
                output.append(book)
    return output
