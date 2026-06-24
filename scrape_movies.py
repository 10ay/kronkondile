from urllib.parse import quote_plus
import webbrowser
from engine.movie_graph import tmdb_search_url

class Movies:
    def __init__(self, title, year, url):
        self.title = title
        self.year = year
        self.url = url

def movie_from_library(movie_title):
    from movie_library import mood_movie_map
    target = movie_title.strip().lower()
    for playlist in mood_movie_map.values():
        for movie in playlist:
            if movie.get("title", "").strip().lower() == target:
                return movie
    return None

def open_movie_on_tmdb(movie):
    entry = movie_from_library(movie)
    if entry:
        title = entry["title"]
        year = entry.get("year")
        url = entry["url"]
    else:
        title = movie
        year = None
        url = tmdb_search_url(movie)
    webbrowser.open(url)
    return Movies(title=title, year=year, url=url)