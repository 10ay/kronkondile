'''
Script used to create table of recently book recommendations.
'''
from engine.book_graph import goodreads_book_url
from typing import Any
from urllib.parse import quote_plus
import webbrowser 

goodreads_search_suffix = ""

class Books:
    def __init__(self, title, author, url):
        self.title = title
        self.author = author
        self.url = url
        


def build_search_url(search_term):
    """
    Build a Goodreads search URL for a book.
    """
    query = f"{search_term} {goodreads_search_suffix}".strip()
    return goodreads_book_url(query)

def book_query(search_term):
    title = f"Goodreads search: {search_term}"
    author = None
    url = build_search_url(search_term)
    return Books(title, author, url)

def open_goodreads(search_term):
    """
    Query to open Goodreads
    """
    url = build_search_url(search_term)
    webbrowser.open(url)
    return book_query(search_term)

def open_goodreads_book(title, url, author=None):
    """
    Open a specific Goodreads book
    """
    webbrowser.open(url)
    return Books(title, author, url)

def open_search(search_term):
    """Open a Goodreads search in the default browser."""
    url = build_search_url(search_term)
    webbrowser.open(url)
    return book_query(search_term)

def book_recommendation(search_term_library):
    if not search_term_library:
        return []
    books = []
    for i in range(len(search_term_library)):
        term = search_term_library[i]
        book = open_search(term)
        books.append(book)
    return books

def open_book_from_dict(book):
    return open_goodreads_book(
        title=book["title"],
        url=book["url"],
        author=book.get("author"),
    )

def book_from_library(book_title):
    """First book in book_library whose title matches."""
    from book_library import mood_book_map
    target = book_title.strip().lower()
    for playlist in mood_book_map.values():
        for book in playlist:
            if book.get("title", "").strip().lower() == target:
                return book
    return None

def open_book_on_goodreads(book):

    entry = book_from_library(book)
    if entry:
        url = entry["url"]
        author = entry.get("author")
        title = entry["title"]
    else:
        url = goodreads_book_url(book)
        author = None
        title = book
    webbrowser.open(url)
    return Books(title=title, author=author, url=url)




if __name__ == "__main__":
    recs = book_recommendation(["Call Me By Your Name"])
    if recs:
        print(f"Opened: {recs[0].url}")
