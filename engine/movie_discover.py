from __future__ import annotations
import random
from engine.movie_graph import load_graph, default_graph_path
from engine.movie_seeds import *
from engine.movie_ratings import *

class Discover:
    def __init__(self, graph, history_likes=None, history_dislikes=None,
                 today_seen=None, movies_today_liked_set=None, all_time_favorites=None):
        self.graph = graph
        self.like = set()
        self.dislike = set()
        self.seen = set()
        self.history_likes = set(history_likes or [])
        self.history_dislikes = set(history_dislikes or [])
        self.today_seen = set(today_seen or [])
        self.movies_today_liked = set(movies_today_liked_set or [])
        self.all_time_favorites = set(all_time_favorites or [])
        self.seed_movie = None

    @classmethod
    def from_file(cls, path=default_graph_path):
        return cls(load_graph(path))

    @classmethod
    def from_file_with_history(cls, mood_index, path=default_graph_path):
        from engine.movie_graph import ensure_movie_graph
        return cls(
            ensure_movie_graph(path),
            history_likes=liked_from_history(mood_index),
            history_dislikes=disliked_from_history(mood_index),
            today_seen=movies_today(mood_index),
            movies_today_liked_set=movies_today_liked(mood_index),
            all_time_favorites = all_time_favorites(mood_index),
        )

    def taste_profile(self):
        return self.like | self.history_likes

    def blocked(self):
        return self.seen | self.dislike | self.history_dislikes | self.today_seen

    def rate_movie(self, movie, rating):
        self.seen.add(movie)
        if rating == "like":
            self.like.add(movie)
            self.dislike.discard(movie)
        elif rating == "dislike":
            self.like.discard(movie)
            self.dislike.add(movie)
        elif rating == "unknown":
            self.like.discard(movie)
            self.dislike.discard(movie)
        else:
            raise ValueError(f"Unknown rating: {rating}")

    def candidate_scores(self):
        scores = {}
        for liked in self.taste_profile():
            for neighbor, weight in self.graph.get(liked, {}).items():
                if neighbor in self.blocked():
                    continue
                scores[neighbor] = scores.get(neighbor, 0) + weight

        if self.seed_movie:
            for neighbor, weight in self.graph.get(self.seed_movie, {}).items():
                if neighbor in self.blocked():
                    continue
                scores[neighbor] = scores.get(neighbor, 0) + weight * 2.0
                for _ in self.history_likes:
                    scores[neighbor] += weight * 0.5
                for _ in self.like:
                    scores[neighbor] += weight * 1.0
                scores[neighbor] = scores.get(neighbor, 0) + weight * 3.0

        return sorted(scores.items(), key=lambda x: (-x[1], x[0]))

    def next_movie(self):
        # First hop: go to seed's best neighbor
        if self.seed_movie and len(self.seen) == 1:
            neighbors = [
                (n, w) for n, w in self.graph.get(self.seed_movie, {}).items()
                if n not in self.blocked()
            ]
            if neighbors:
                neighbors.sort(key=lambda x: (-x[1], x[0]))
                movie = neighbors[0][0]
                self.seen.add(movie)
                return movie

        ranked = self.candidate_scores()
        if not ranked:
            return None
        movie, _score = ranked[0]
        self.seen.add(movie)
        return movie