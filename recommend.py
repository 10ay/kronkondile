"""
Turn today's mood into a list of music recommendations.
"""

from scrape_music import Tracks, track_recommendation, open_song_from_dict

import pandas as pd
import random
import os

from feelings import FEELINGS_FILE, feelings_dictionary
from music_library import spotify_lovesick, spotify_mountains, spotify_silly, spotify_minions, spotify_love
from music_library import mood_music_map

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

def mood_to_music(feeling_index, rand_int = -1):
    """
    Maps your mood to a music dictionary.
    """
    if feeling_index not in feelings_dictionary:
        raise ValueError()
   # import pdb; pdb.set_trace()
    if rand_int != -1:
        rand_int = rand_int
    else:
        rand_int = random.randint(0, 9)
    #import pdb; pdb.set_trace()
    return mood_music_map[feeling_index][rand_int]

def get_recommendations_for_mood(feeling_index, rand_int = -1):
    """
    Music recommendations for a given mood.
    """
    music_terms_to_search = mood_to_music(feeling_index, rand_int)
    track = open_song_from_dict(music_terms_to_search)
    return [track]

    return track_recommendation(music_terms_to_search)

def get_recommendations(rand_int = -1):
    """
    Get music recommendations for today.
    """
    feeling_index, feeling_name = get_feeling()
    if feeling_index is None:
        return []
    return get_recommendations_for_mood(feeling_index, rand_int)


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
