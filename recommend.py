"""
Turn today's mood into a list of music recommendations.
"""

from scrape_music import Tracks, track_recommendation, open_song_from_dict

import pandas as pd
import random
import os

from feelings import FEELINGS_FILE

feelings_dictionary = {
    0 : "bad", 
    1 : "not the best", 
    2 : "neutral", 
    3 : "satisfactory", 
    4 : "good!"}

from music_library import spotify_bad, spotify_not_the_best, spotify_neutral, spotify_satisfactory, spotify_good


mood_music_map = {
    0: spotify_bad,
    1: spotify_not_the_best,
    2: spotify_neutral,
    3: spotify_satisfactory,
    4: spotify_good
}

def get_feeling():
    """
    Get how you feel today.
    """
    if not os.path.exists(FEELINGS_FILE):
        print("Why do you have no feelings today?")
        return None
    df = pd.read_csv(FEELINGS_FILE, sep = '\t', names = ['feeling_scale', 'date'])
    if df.empty:
        print("Why do you have no feelings today?")
        return None
    else:
        feeling_index = int(df.iloc[-1]['feeling_scale'])
        return feeling_index, feelings_dictionary[feeling_index]

def mood_to_music(feeling_index):
    """
    Maps your mood to a music dictionary.
    """
    if feeling_index not in feelings_dictionary:
        raise ValueError()
    rand_int = random.randint(0, 4)
    return mood_music_map[feeling_index][rand_int]

def get_recommendations_for_mood(feeling_index):
    """
    Music recommendations for a given mood.
    """
    music_terms_to_search = mood_to_music(feeling_index)
    track = open_song_from_dict(music_terms_to_search)
    return [track]

    return track_recommendation(music_terms_to_search)

def get_recommendations():
    """
    Get music recommendations for today.
    """
    feeling_index, feeling_name = get_feeling()
    if feeling_index is None:
        return []
    return get_recommendations_for_mood(feeling_index)


def format_recommendations(recommendations, feeling_name=None):
    """
    Format music recommendations. print in terminal.
    """
    lines = []
    if feeling_name is not None:
        lines.append(f"Feeling: {feeling_name}")
    
    if not recommendations:
        lines.append("Mood is a concept you cannot comprehend.")
        return "\n".join(lines)

    lines.append("Opened YouTube:\n")

    for track in recommendations:
        lines.append(track.title)
        lines.append(f"  {track.url}\n")

    return "\n".join(lines)


if __name__ == "__main__":
    feeling_index, feeling_name = get_feeling()
    recs = get_recommendations()
    print(format_recommendations(recs, feeling_name=feeling_name))
