from __future__ import annotations
from engine.graph import Graph, load_graph, default_graph_path
from recommend import *
from engine.seeds import *

class Discover:
    def __init__(self, graph):
        self.graph = graph
        self.like = set()
        self.dislike = set()
        self.seen = set()
    @classmethod
    def from_file(cls, path = default_graph_path):
        return cls(load_graph(path))

    

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

        for like in self.like:
            for neighbor, weight in self.graph.get(like, {}).items():
                if neighbor in self.seen or neighbor in self.dislike:
                    continue
                scores[neighbor] = scores.get(neighbor, 0) + weight #Weight to add additional weight to two common artists being present
        
        ranked = sorted(scores.items(), key=lambda x: (-x[1], x[0]))
        return ranked

    def next_artist(self):
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

