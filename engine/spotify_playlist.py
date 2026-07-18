"""
Spotify playlists
"""

from __future__ import annotations
import requests

api = "https://api.spotify.com/v1"


def headers(token):
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


def search_track(token, title, artist):
    failed = None
    for query in (f"track:{title} artist:{artist}", f"{title} {artist}"):
        response = requests.get(
            f"{api}/search",
            headers=headers(token),
            params={"q": query, "type": "track", "limit": 1},
            timeout=10,
        )
        if response.status_code != 200:
            print(f"Spotify search {response.status_code} for {title!r}: {response.text[:200]}")
            failed = response
            continue
        items = response.json().get("tracks", {}).get("items", [])
        if items:
            return items[0]["uri"]
    # A real "no match" returns None; an API error (401/403/429) should not
    # be mistaken for one.
    if failed is not None:
        failed.raise_for_status()
    return None


def create_playlist(token, name, description=""):
    response = requests.post(
        f"{api}/me/playlists",
        headers=headers(token),
        json={"name": name, "public": False, "description": description},
        timeout=10,
    )
    response.raise_for_status()
    payload = response.json()
    return payload["id"], payload["external_urls"]["spotify"]


def add_tracks(token, playlist_id, uris):
    response = requests.post(
        f"{api}/playlists/{playlist_id}/items",
        headers=headers(token),
        json={"uris": uris},
        timeout=10,
    )
    response.raise_for_status()


def publish_mood_playlist(token, tracks, name, description=""):
    uris = []
    for t in tracks:
        uri = search_track(token, t["title"], t["artist"])
        if uri:
            uris.append(uri)
    print(f"Found {len(uris)}/{len(tracks)} tracks on Spotify")
    if not uris:
        return None
    playlist_id, url = create_playlist(token, name, description=description)
    add_tracks(token, playlist_id, uris)
    return url
