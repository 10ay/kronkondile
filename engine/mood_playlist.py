from engine.graph import *
from engine.seeds import *
from engine.ratings import *
from frontend.scrape_music import song_from_library
import random

lastfm_url = "https://ws.audioscrobbler.com/2.0/"

root = Path(__file__).resolve().parent.parent
tag_cache_path = root / "data" / "lastfm_tag_cache.json"

# Hops and weights
activity_list = [
    "Focus",
    "Relax",
    "Workout",
    "Party",
    "Drive",
    "Work", 
    "Sleep",
]

acitivity_default_tempo = {
    "Focus": "slow",
    "Relax": "slow",
    "Workout" : "fast",
    "Party" : "fast",
    "Drive" : "fast",
    "Work" : "slow", 
    "Sleep" : "slow",
}

genres = [
    "any", "indie", "folk", "pop", "rock", "alternative", "rnb", "metal", "jazz", "lo-fi", "classical"
]

slow_tags = {
    "slow", "slowcore", "ballad", "ambient", "chill", "acoustic",
    "dream pop", "dreampop", "soft", "mellow", "lullaby", "sad",
    "melancholy", "folk", "chamber pop",
}

fast_tags = {
    "fast", "dance", "electronic", "punk", "metal", "upbeat",
    "energetic", "party", "disco", "edm", "techno", "house",
    "power pop", "garage", "hardcore",
}


def mood_seed_artists(mood_index):
    seeds = list(seed_by_mood().get(mood_index, []))
    for a in all_time_favorites(mood_index):
        if a not in seeds:
            seeds.append(a)
    for a in liked_from_history(mood_index):
        if a not in seeds:
            seeds.append(a)
    return seeds



def load_tag_cache():
    if tag_cache_path.exists():
        return json.loads(tag_cache_path.read_text(encoding="utf-8"))
    return {}

def save_tag_cache(cache):
    tag_cache_path.parent.mkdir(parents=True, exist_ok=True)
    tag_cache_path.write_text(json.dumps(cache, indent=2), encoding="utf-8")

def fetch_artist_tags(artist, api_key, limit=12):

    cache = load_tag_cache()
    key = artist.strip().lower()
    if key in cache:
        return [str(t).lower() for t in cache[key]]
    params = {
        "method": "artist.getTopTags",
        "artist": artist,
        "api_key": api_key,
        "format": "json",
    }
    try:
        response = requests.get(lastfm_url, params=params, timeout=10)
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException:
        return []
    raw = payload.get("toptags", {}).get("tag", [])
    if isinstance(raw, dict):
        raw = [raw]
    tags = []
    for item in raw[:limit]:
        name = str(item.get("name", "")).strip().lower()
        if name:
            tags.append(name)
    cache[key] = tags
    save_tag_cache(cache)
    time.sleep(0.15)
    return tags

def matches_genre(tags, genre): 
    if not genre or genre == "any":
        return True
    gen = genre.strip().lower()
    return any(gen == tag or gen in tag or tag in gen for tag in tags)

def matches_tempo(tags, tempo):
    tempo = (tempo or "slow").strip().lower()
    if tempo not in ("slow", "fast"):
        tempo = "slow"
    
    tagset = set(tags)
    slow_hits = len(tagset & slow_tags)
    fast_hits = len(tagset & fast_tags)

    if tempo == "slow":
        if fast_hits > 0 and slow_hits == 0:
            return False
        else:
            return True
        
    if slow_hits > 0 and fast_hits == 0:
        return False
    return True


def collect(graph, seeds, blocked):
    scores: dict[str, float] = {}
    blocked = set(blocked or [])
    seed_set = set(seeds)

    for seed in seeds:
        if seed not in blocked:
            scores[seed] = scores.get(seed, 0.0) + 10.0
        for neighbor, w in graph.get(seed, {}).items():
            if neighbor in seed_set or neighbor in blocked:
                continue
            scores[neighbor] = scores.get(neighbor, 0.0) + float(w)

    return sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))

def generate_mood_playlist(mood_index, activity = "none", genre = "any", tempo = "slow", length = 15, graph = None):
    if graph is None:
        graph = load_graph(default_graph_path)

    activity_raw = (activity or "none").strip()
    matched = next(
        (a for a in activity_list if a.lower() == activity_raw.lower()),
        None,
    )
    activity = matched if matched is not None else "none"

    genre = (genre or "any").strip().lower()
    tempo = (tempo or "slow").strip().lower()
    if tempo not in ("slow", "fast"):
        tempo = "slow"

    seeds = [s for s in mood_seed_artists(mood_index) if s in graph]
    if not seeds:
        return {
            "mood_index": mood_index,
            "activity": activity,
            "genre": genre,
            "tempo": tempo,
            "seeds_used": [],
            "artists": [],
            "error": "No mood seeds found in artist_graph.json",
        }

    blocked = disliked_from_history(mood_index)
    ranked = collect(graph, seeds, blocked)
   # import pdb; pdb.set_trace()
    api_key = get_api()

    
    playlist = []
    for artist, _score in ranked:
        if artist in playlist:
            continue
        if api_key:
            tags = fetch_artist_tags(artist, api_key)
            if tags:
                if not matches_genre(tags, genre):
                    continue
                if not matches_tempo(tags, tempo):
                    continue
        playlist.append(artist)
        if len(playlist) >= length:
            break

    return {
        "mood_index": mood_index,
        "activity": activity,
        "genre": genre,
        "tempo": tempo,
        "seeds_used": seeds,
        "artists": playlist[:length],
        "error": None,
    }





def song_for_artist(artist):
    """
    Returns {title, artist, lastfm_url} for one playlist row.
    """
    song = song_from_library(artist)
    if song:
        title = song["title"]
        art = song.get("artist") or artist
        return {
            "title": title,
            "artist": art,
            "lastfm_url": lastfm_track_url(art, title),
        }
    try:
        top = fetch_top_track(artist, get_api(), limit=1)
        if top:
            return {
                "title": top,
                "artist": artist,
                "lastfm_url": lastfm_track_url(artist, top),
            }
    except Exception:
        pass
    return {
        "title": artist,
        "artist": artist,
        "lastfm_url": lastfm_artist_url(artist),
    }

def songs_from_artists(artists):
    return [song_for_artist(a) for a in artists]
