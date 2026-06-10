'''
Script used to create table of recently music recommendations.
'''
from typing import Any
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
max_recommendations = 10 # Change this for the number of recommendations you want to scrape.

import webbrowser 
from urllib.parse import quote_plus

import webbrowser
from urllib.parse import quote_plus

youtube_search_suffix = "music"
# constant selectors to look up videos on youtube search page. This is how Youtube's HTML is structured in nested elements.
video_row = "ytd-video-renderer"
video_title = "h3 a#video-title, a#video-title"
video_channel = "a#channel-name, ytd-channel-name a"

class Tracks:
    def __init__(self, title, artist, url, channel):
        self.title = title
        self.artist = artist
        self.url = url
        self.channel = channel
        


def build_search_url(search_term):
    """
    Build a YouTube search URL for a mood/genre term.
    search_term will eventually come from feelings.py via MOOD_TO_MUSIC.
    """
    query = f"{search_term} {youtube_search_suffix}".strip()
    return f"https://www.youtube.com/results?search_query={quote_plus(query)}"

def track_query(search_term):
    title = f"YouTube search: {search_term}"
    artist = None
    url = build_search_url(search_term)
    channel = None
    return Tracks(title, artist, url, channel)

def open_youtube(search_term):
    """
    Query to open YouTube
    """
    url = build_search_url(search_term)
    webbrowser.open(url)
    return track_query(search_term)

def open_youtube_song(title, url, artist=None):
    """
    Open a specific Youtube Song
    """
    webbrowser.open(url)
    return Tracks(title, artist, url, channel=None)

def open_search(search_term):
    """Open a YouTube search in the default browser."""
    url = build_search_url(search_term)
    webbrowser.open(url)
    return track_query(search_term)

def track_recommendation(search_term_library):
    if not search_term_library:
        return []
    tracks = []
    for i in range(len(search_term_library)):
        term = search_term_library[i]
        track = open_search(term)
        tracks.append(track)
    return tracks

def open_song_from_dict(song):
    return open_youtube_song(
        title=song["title"],
        url=song["url"],
        artist=song.get("artist"),
    )

if __name__ == "__main__":
    recs = track_recommendation(["chill"])
    if recs:
        print(f"Opened: {recs[0].url}")
