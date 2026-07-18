from frontend.movie_library import mood_movie_map

def pull_movie(movies):
    """Pull a movie. Unique movie """
    seen = set()
    titles = []
    for movie in movies:
        movie_name = movie["title"]
        if movie_name and movie_name not in seen:
            seen.add(movie_name)
            titles.append(movie_name)
    return titles

def seed_by_mood():
    """
    Map mood to movie
    """
    return {mood: pull_movie(playlist) for mood, playlist in mood_movie_map.items()}


def movie_for_each_seed():
    """
    Flatten the 25 movies.
    """
    seen = set()
    output = []
    for movies in seed_by_mood().values():
        for movie in movies:
            if movie not in seen:
                seen.add(movie)
                output.append(movie)
    return output
