from frontend.music_library import mood_music_map

def pull_artist(songs):
    """Pull an artist. Unique artist """
    seen = set()
    artists = []
    for song in songs:
        artist_name = song["artist"]
        if artist_name and artist_name not in seen:
            seen.add(artist_name)
            artists.append(artist_name)
    return artists

def seed_by_mood():
    """
    Map mood to artist
    """
    return {mood: pull_artist(playlist) for mood, playlist in mood_music_map.items()}


def artist_for_each_seed():
    """
    Flatten the 25 artists.
    """
    seen = set()
    output = []
    for artists in seed_by_mood().values():
        for artist in artists:
            if artist not in seen:
                seen.add(artist)
                output.append(artist)
    return output
