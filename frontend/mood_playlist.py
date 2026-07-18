"""
Mood playlist
"""

from __future__ import annotations

import html
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from frontend.feelings import feelings_dictionary
from frontend.recommend import get_feeling
from engine.mood_playlist import (
    acitivity_default_tempo,
    activity_list,
    generate_mood_playlist,
    genres,
    songs_from_artists,
)
from engine.spotify_auth import (
    authorize_url,
    exchange_code,
    load_client_id,
    new_verifier,
    save_client_id,
    valid_client_id,
)
from engine.spotify_playlist import publish_mood_playlist


root = Path(__file__).resolve().parent.parent
template_path = root / "static" / "mood_playlist.html"
spotify_form_path = root / "static" / "spotify_form.html"
out_path = root / "data" / "mood_playlist.html"

server_port = 8888
spotify_lock = threading.Lock()
spotify_state = {
    "tracks": [],
    "name": "",
    "description": "",
    "client_id": "",
    "verifier": "",
    "url": None,
    "done": False,
    "page": "",
    "publishing": False,
}


def load_template():
    if not template_path.exists():
        raise FileNotFoundError(f"Missing template: {template_path}")
    return template_path.read_text(encoding="utf-8")


def render_playlist_html(tracks, mood_label, meta, out_path, spotify_button=""):
    cards = []
    for t in tracks:
        cards.append(f"""
                <article class="track">
                <div class="info">
                    <div class="title">{html.escape(t["title"])}</div>
                    <div class="artist">{html.escape(t["artist"])}</div>
                </div>
                <div class="actions">
                    <a href="{html.escape(t["lastfm_url"])}" target="_blank" rel="noopener">Last.fm</a>
                </div>
                </article>""")

    page = load_template()
    page = page.replace("<!--MOOD_LABEL-->", html.escape(mood_label))
    page = page.replace("<!--META-->", html.escape(meta))
    page = page.replace("<!--SPOTIFY-->", spotify_button)
    page = page.replace("<!--TRACKS-->", "\n".join(cards))

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(page, encoding="utf-8")
    return out_path


def name_form_html(error=""):
    saved_client_id = load_client_id()
    page = spotify_form_path.read_text(encoding="utf-8")
    error_message = f'<p class="error">{html.escape(error)}</p>' if error else ""
    page = page.replace("<!--ERROR-->", error_message)
    page = page.replace("<!--SETUP_OPEN-->", "" if saved_client_id else "open")
    page = page.replace("<!--CLIENT_ID-->", html.escape(saved_client_id))
    return page


class SpotifyClickHandler(BaseHTTPRequestHandler):
    timeout = 15

    def log_message(self, fmt, *args):
        print(f"[spotify] {fmt % args}")

    def send_html(self, status, body):
        data = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(data)

    def redirect(self, url):
        self.send_response(302)
        self.send_header("Location", url)
        self.send_header("Connection", "close")
        self.end_headers()

    def start_login(self):
        verifier = new_verifier()
        spotify_state["verifier"] = verifier
        print("Opening Spotify login...")
        self.redirect(authorize_url(
            spotify_state["client_id"],
            verifier,
        ))

    def publish(self, token):
        name = (spotify_state.get("name") or "").strip()
        description = (spotify_state.get("description") or "").strip()
        if not name or not description:
            self.send_html(200, name_form_html("Enter a playlist name and description."))
            return
        print(f"Building Spotify playlist: {name!r}")
        url = publish_mood_playlist(
            token,
            spotify_state["tracks"],
            name,
            description=description,
        )
        spotify_state["url"] = url
        spotify_state["done"] = True
        if url:
            print(f"Playlist created: {url}")
            self.redirect(url)
        else:
            self.send_html(200, "<h1>No tracks matched on Spotify</h1>")

    def handle_callback(self, code):
        # Browser sometimes hits /callback twice; only exchange once.
        with spotify_lock:
            if spotify_state["url"]:
                self.redirect(spotify_state["url"])
                return
            if spotify_state["publishing"]:
                self.send_html(200, "<h1>Building your Spotify playlist...</h1>")
                return
            spotify_state["publishing"] = True

        try:
            print("Spotify login OK")
            self.publish(exchange_code(
                code,
                spotify_state["client_id"],
                spotify_state["verifier"],
            ))
        except Exception:
            with spotify_lock:
                spotify_state["publishing"] = False
            raise

    def do_GET(self):
        parsed = urlparse(self.path)
        try:
            if parsed.path in ("/", "/index.html"):
                self.send_html(200, spotify_state.get("page") or "<h1>No playlist</h1>")
            elif parsed.path == "/save":
                print("Save on Spotify clicked")
                self.send_html(200, name_form_html())
            elif parsed.path == "/callback":
                code = parse_qs(parsed.query).get("code", [None])[0]
                if not code:
                    spotify_state["done"] = True
                    self.send_html(400, "<h1>Spotify login cancelled</h1>")
                    return
                self.handle_callback(code)
            else:
                self.send_response(404)
                self.send_header("Connection", "close")
                self.end_headers()
        except Exception as e:
            print(f"Spotify error: {e}")
            spotify_state["done"] = True
            self.send_html(500, f"<h1>Spotify error</h1><pre>{html.escape(str(e))}</pre>")

    def do_POST(self):
        parsed = urlparse(self.path)
        try:
            if parsed.path != "/save":
                self.send_response(404)
                self.send_header("Connection", "close")
                self.end_headers()
                return
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length).decode("utf-8") if length else ""
            fields = parse_qs(raw)
            name = (fields.get("name", [""])[0] or "").strip()
            description = (fields.get("description", [""])[0] or "").strip()
            client_id = (fields.get("client_id", [""])[0] or "").strip()
            if not name or not description:
                self.send_html(200, name_form_html("Playlist name and description are required."))
                return
            if not valid_client_id(client_id):
                self.send_html(200, name_form_html("Enter the 32-character Client ID from your Spotify app."))
                return
            save_client_id(client_id)
            spotify_state["name"] = name
            spotify_state["description"] = description
            spotify_state["client_id"] = client_id
            print(f"Playlist name: {name!r}")
            print(f"Playlist description: {description!r}")
            self.start_login()
        except Exception as e:
            print(f"Spotify error: {e}")
            spotify_state["done"] = True
            self.send_html(500, f"<h1>Spotify error</h1><pre>{html.escape(str(e))}</pre>")


def wait_for_spotify_click(timeout_seconds=300):
    httpd = ThreadingHTTPServer(("127.0.0.1", server_port), SpotifyClickHandler)
    httpd.daemon_threads = True
    deadline = time.time() + timeout_seconds
    print(f"\nPlaylist page: http://127.0.0.1:{server_port}/")
    print("Click 'Save on Spotify' (Ctrl+C to skip)...")
    webbrowser.open(f"http://127.0.0.1:{server_port}/")
    try:
        while not spotify_state["done"] and time.time() < deadline:
            httpd.handle_request()
    except KeyboardInterrupt:
        print("Skipped Spotify.")
    finally:
        httpd.server_close()
    if spotify_state["url"]:
        print(f"Done: {spotify_state['url']}")
    elif not spotify_state["done"]:
        print("Timed out waiting for Spotify click.")

def pick_activity():
    print("\nActivity:")
    for i, name in enumerate(activity_list):
        print(f"  [{i}] {name}")
    raw = input("Activity [0=none]: ").strip()
    try:
        idx = int(raw) if raw else 0
    except ValueError:
        idx = 0
    if idx < 0 or idx >= len(activity_list):
        idx = 0
    return activity_list[idx]


def pick_genre():
    print("\nGenre:")
    for i, g in enumerate(genres):
        print(f"  [{i}] {g}")
    raw = input("Genre [0=any]: ").strip()
    try:
        idx = int(raw) if raw else 0
    except ValueError:
        idx = 0
    if idx < 0 or idx >= len(genres):
        idx = 0
    return genres[idx]


def pick_tempo(default="slow"):
    print("\nTempo:")
    print("  [1] slow")
    print("  [2] fast")
    hint = "1" if default == "slow" else "2"
    raw = input(f"Tempo [{hint}={default}]: ").strip()
    if not raw:
        return default
    if raw == "2":
        return "fast"
    if raw == "1":
        return "slow"
    return default


def main():
    print("\n=== Mood Playlist Generator ===")

    feeling_index, feeling_name = get_feeling()
    mood = feeling_index

    activity = pick_activity()
    genre = pick_genre()
    tempo_default = acitivity_default_tempo.get(activity, "slow")
    tempo = pick_tempo(default=tempo_default)

    length_raw = input("How many tracks? [20]: ").strip()
    try:
        length = max(5, int(length_raw)) if length_raw else 20
    except ValueError:
        length = 20

    print("\nBuilding playlist...")
    print(f"Mood: {feeling_name}")
    result = generate_mood_playlist(mood, activity, genre, tempo, length)

    if result.get("error"):
        print(result["error"])
        return
    if not result["artists"]:
        print("No artists found.")
        return

    print(f"Resolving songs for {len(result['artists'])} artists...")
    tracks = [t for t in songs_from_artists(result["artists"]) if t]

    meta = (
        f"{len(tracks)} tracks · activity={result['activity']} · "
        f"genre={result['genre']} · tempo={result['tempo']}"
    )

    spotify_state["tracks"] = tracks
    spotify_state["name"] = ""
    spotify_state["description"] = ""
    spotify_state["client_id"] = ""
    spotify_state["verifier"] = ""
    spotify_state["url"] = None
    spotify_state["done"] = False
    spotify_state["publishing"] = False

    path = render_playlist_html(
        tracks,
        mood_label=feelings_dictionary[mood],
        meta=meta,
        out_path=out_path,
        spotify_button='<a class="spotify-save" href="/save">Save on Spotify</a>',
    )
    spotify_state["page"] = path.read_text(encoding="utf-8")
    print(f"\nSaved {path}")

    wait_for_spotify_click()


if __name__ == "__main__":
    main()
