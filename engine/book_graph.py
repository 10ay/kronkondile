"""
Build a book graph.
Use Open Library API to get book data. 

python -c "
from engine.book_graph import get_api, fetch_sim_books
for name, weight in fetch_sim_books('Call Me By Your Name', get_api(), limit=15):
    print(f'{name:30} {weight:.2f}')
"
"""


from __future__ import annotations
import json, os, re, time
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus
import requests

Graph = dict[str, dict[str, float]]

root = Path(__file__).resolve().parent.parent
default_graph_path = root / "data" / "book_graph.json"

openlibrary_url = "https://openlibrary.org/"

goodreads_base = "https://www.goodreads.com/search"

def goodreads_book_url(book: str) -> str:
    return f"{goodreads_base}?q={quote_plus(book)}"



def get_api():
    return ""

def cache_path():
    return root / "data" / "openlibrary_cache.json"

def cache_key(book):
    return book.strip().lower()

def load_cache():
    path = cache_path()
    if path.exists():
        return json.loads(path.read_text())
    return {}

def save_cache(cache):
    path = cache_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cache, indent=2))

def author_for_book(book):
    from book_library import mood_book_map
    target = book.strip().lower()
    for playlist in mood_book_map.values():
        for entry in playlist:
            if entry.get("title", "").strip().lower() == target:
                return entry.get("author")
    return None

def get_json(url, params=None, retries=3):
    headers = {"User-Agent": "kronkondile/1.0 (local book discover)"}
    last_error = None
    for attempt in range(retries):
        try:
            response = requests.get(url, params=params, headers=headers, timeout=20)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            last_error = exc
            time.sleep(0.4 * (attempt + 1))
    raise last_error

def normalize_title(title):
    return re.sub(r"\s+", " ", title.strip().lower())

def subject_slug(subject):
    return re.sub(r"[^a-z0-9]+", "_", subject.strip().lower()).strip("_")

def normalize_subjects(raw):
    subjects = []
    for item in raw or []:
        if isinstance(item, str):
            subjects.append(item.strip())
        elif isinstance(item, dict):
            name = str(item.get("name", "")).strip()
            if name:
                subjects.append(name)
    return [s for s in subjects if s]

def search_work(title, author=None):
    params = {
        "title": title,
        "limit": 8,
        "fields": "key,title,subject,author_name",
    }
    if author:
        params["author"] = author
    payload = get_json(f"{openlibrary_url}search.json", params)
    docs = payload.get("docs", [])
    if not docs:
        return None
    target = normalize_title(title)
    for doc in docs:
        if normalize_title(str(doc.get("title", ""))) == target:
            return doc
    return docs[0]

def work_subjects(work_key, search_doc=None):
    subjects = normalize_subjects((search_doc or {}).get("subject"))
    if subjects:
        return subjects[:12]
    if not work_key.startswith("/"):
        work_key = "/" + work_key
    payload = get_json(f"https://openlibrary.org{work_key}.json")
    return normalize_subjects(payload.get("subjects"))[:12]

def books_for_subject(subject, limit):
    slug = subject_slug(subject)
    if not slug:
        return []
    payload = get_json(
        f"{openlibrary_url}subjects/{quote_plus(slug)}.json",
        {"limit": limit},
    )
    titles = []
    for work in payload.get("works", []):
        title = str(work.get("title", "")).strip()
        if title:
            titles.append(title)
    return titles

def fetch_sim_books(book, api_key, limit):
    author = author_for_book(book)
    cache = load_cache()
    book_key = cache_key(book)
    cache_entry_key = f"{book_key}|{cache_key(author or '')}"
    if cache_entry_key in cache:
        return [(title, float(score)) for title, score in cache[cache_entry_key][:limit]]

    work_doc = search_work(book, author=author)
    if not work_doc:
        return []

    work_key = str(work_doc.get("key", "")).strip()
    if not work_key:
        return []

    subjects = work_subjects(work_key, work_doc)
    if not subjects:
        author_names = work_doc.get("author_name") or []
        if author_names:
            payload = get_json(
                f"{openlibrary_url}search.json",
                {
                    "author": author_names[0],
                    "limit": max(limit, 20),
                    "fields": "title",
                },
            )
            scores = {}
            for doc in payload.get("docs", []):
                title = str(doc.get("title", "")).strip()
                if not title or cache_key(title) == book_key:
                    continue
                scores[title] = 0.35
            ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
            result = ranked[:limit]
            cache[cache_entry_key] = [[title, score] for title, score in result]
            save_cache(cache)
            return result
        return []

    subject_set = {subject_slug(s) for s in subjects if subject_slug(s)}
    candidate_scores = {}

    per_subject = max(8, limit // max(len(subjects[:6]), 1))
    for subject in subjects[:6]:
        for title in books_for_subject(subject, per_subject):
            title_key = cache_key(title)
            if title_key == book_key:
                continue
            candidate_scores[title] = candidate_scores.get(title, 0.0) + 1.0
        time.sleep(0.15)

    ranked = []
    for title, hits in candidate_scores.items():
        score = hits / max(len(subject_set), 1)
        ranked.append((title, min(score, 1.0)))

    ranked.sort(key=lambda item: (-item[1], item[0]))
    result = ranked[:limit]

    cache[cache_entry_key] = [[title, score] for title, score in result]
    save_cache(cache)
    return result


    
###############################################################
#Build graphs connecting books to their similar books now.#
###############################################################

def ensure_node(graph, book):
    graph.setdefault(book, {})

def add_edge(graph, book_a, book_b, weight):
    """
    If book a is close to b, b is close to a.
    Keep the heigher weight if we see the same pair twice
    """
    if book_a == book_b or weight <= 0:
        return
    else:
        ensure_node(graph, book_a)
        ensure_node(graph, book_b)

    graph[book_a][book_b] = max(graph[book_a].get(book_b, 0.0), weight)
    graph[book_b][book_a] = max(graph[book_b].get(book_a, 0.0), weight)

def build_graph_from_seeds(seed_books, api_key, neighbors_per_seed = 20, pause_seconds = 0.25):
    graph = {}
    for i, seed in enumerate(seed_books, start = 1):
        ensure_node(graph, seed)
        try:
            neighbors = fetch_sim_books(seed, api_key, neighbors_per_seed)
        except requests.RequestException:
            continue

        for neigbor, weight in neighbors:
            add_edge(graph, seed, neigbor, weight)

        if pause_seconds>0:
            time.sleep(pause_seconds)
        
    return graph 

def save_graph(graph, path):
    """
    Save the graph to a file
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(graph, indent=2))
    return path

def load_graph(path):
    """
    Load the graph from a file.
    """
    if not path.exists():
        raise FileNotFoundError()
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        raise FileNotFoundError()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        raise FileNotFoundError()

def graph_statistics(graph):
    edges = sum(len(neighbors) for neighbors in graph.values()) // 2 # Don't repeat edges.
    weights = [w for neighbors in graph.values() for w in neighbors.values()]
    if weights:
        return {
        "books": len(graph),
        "edges": edges,
        "average_weight": round(sum(weights) / len(weights), 3)
        }
    else:
        return {
        "books": len(graph),
        "edges": edges,
        "average_weight": 0.0
        }

def neighbors_of(graph, book, top_k):
    """
    Find closest neighbor to a book 
    k.
    """
    ranked = sorted(graph.get(book, {}).items(), key = lambda item: (-item[1], item[0]))
    return ranked[:top_k]



