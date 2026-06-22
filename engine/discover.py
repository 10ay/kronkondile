from __future__ import annotations
from engine.graph import Graph, load_graph, default_graph_path
from recommend import *
from engine.seeds import *
from engine.ratings import *

class Discover:
    def __init__(self, graph, history_likes = None, history_dislikes = None, today_seen = None, artists_today_liked = None, all_time_favorites = None):
        self.graph = graph
        self.like = set()
        self.dislike = set()
        self.seen = set()
        self.history_likes = set(history_likes or [])
        self.history_dislikes = set(history_dislikes or [])
        self.today_seen = set(today_seen or [])
        self.artists_today_liked = set(artists_today_liked or [])
        self.seed_artist = None
        self.all_time_favorites = set(all_time_favorites or [])

    @classmethod
    def from_file(cls, path = default_graph_path):
        return cls(load_graph(path))

    @classmethod
    def from_file_with_history(cls, mood_index, path=default_graph_path):
        return cls(
        load_graph(path),
        history_likes=liked_from_history(mood_index),
        history_dislikes=disliked_from_history(mood_index),
        today_seen=artists_today(mood_index),
        artists_today_liked=artists_today_liked(mood_index),
        all_time_favorites=all_time_favorites(mood_index))

    def taste_profile(self):
        "Builds a taste profile based on the liked artists from history"
        return self.like | self.history_likes
    
    def blocked(self):
        """
        If an artist is disliked, then they are not recommended.
        """
        return self.seen |self.dislike | self.history_dislikes | self.today_seen

    # Rate the artist on Like, Dislike Or Unknown
    def rate_artist(self, artist, rating):
        self.seen.add(artist)
        if rating == "like":
            self.like.add(artist)
            self.dislike.discard(artist)
        elif rating == "dislike":
            self.like.discard(artist)
            self.dislike.add(artist)
        elif rating == "unknown":
            self.like.discard(artist)
            self.dislike.discard(artist)
        else:
            raise ValueError(f"I am not smart enough to understand this rating yet.")


    # If you like two artsits, an artist connected to these 2 artists gets a higher score.     
    def candidate_scores(self):
        scores: dict[str, float] = {}

        for like in self.taste_profile():
            for neighbor, weight in self.graph.get(like, {}).items():
                if neighbor in self.blocked():
                    continue
                scores[neighbor] = scores.get(neighbor, 0) + weight #Weight to add additional weight to two common artists being present
        
        # I need a seed multiplier here to prioritize seeds over non_seeds
        if self.seed_artist:
            for neighbor, weight in self.graph.get(self.seed_artist, {}).items():
                if neighbor in self.blocked():
                    continue
                scores[neighbor] = scores.get(neighbor, 0) + weight * 2.0  # tune 2.0

                history_weight = 0.5
                session_weight = 1.0
                seed_weight = 3.0
                for like in self.history_likes:
                    scores[neighbor] += weight * history_weight
                for like in self.like:
                    scores[neighbor] += weight * session_weight
                if self.seed_artist:
                    scores[neighbor] = scores.get(neighbor, 0) + weight * seed_weight

                
        ranked = sorted(scores.items(), key=lambda x: (-x[1], x[0]))
        return ranked

    def next_artist(self):
        #First take the seed's immediate neighbor into account
        if self.seed_artist and len(self.seen) == 1:  # only seed shown so far
            neighbors = [(n, w) for n, w in self.graph.get(self.seed_artist, {}).items() if n not in self.blocked()]
            if neighbors:
                neighbors.sort(key=lambda x: (-x[1], x[0]))
                artist = neighbors[0][0]
                self.seen.add(artist)
                return artist
        ranked = self.candidate_scores()
        if not ranked:
            return None
        artist, score = ranked[0]
        self.seen.add(artist)
        return artist

    # If candidate scores empty or no new artist returned, print "Done"

    def random_unseen(self):
        unseen = [artist for artist in self.graph if artist not in self.seen]
        if not unseen:
            return None
        else:
            artist = random.choice(unseen)
            self.seen.add(artist)
            return artist

