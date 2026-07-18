from __future__ import annotations
from engine.book_graph import Graph, load_graph, default_graph_path
from engine.book_seeds import *
from engine.book_ratings import *

class Discover:
    def __init__(self, graph, history_likes = None, history_dislikes = None, today_seen = None, books_today_liked = None):
        self.graph = graph
        self.like = set()
        self.dislike = set()
        self.seen = set()
        self.history_likes = set(history_likes or [])
        self.history_dislikes = set(history_dislikes or [])
        self.today_seen = set(today_seen or [])
        self.books_today_liked = set(books_today_liked or []),
        self.seed_book = None
    @classmethod
    def from_file(cls, path = default_graph_path):
        return cls(load_graph(path))

    @classmethod
    def from_file_with_history(cls, mood_index, path=default_graph_path):
        return cls(
        load_graph(path),
        history_likes=liked_from_history(mood_index),
        history_dislikes=disliked_from_history(mood_index),
        today_seen=books_today(mood_index),
        books_today_liked=books_today_liked(mood_index))

    def taste_profile(self):
        "Builds a taste profile based on the liked books from history"
        return self.like | self.history_likes
    
    def blocked(self):
        """
        If a book is disliked, then it is not recommended.
        """
        return self.seen |self.dislike | self.history_dislikes | self.today_seen

    # Rate the book on Like, Dislike Or Unknown
    def rate_book(self, book, rating):
        self.seen.add(book)
        if rating == "like":
            self.like.add(book)
            self.dislike.discard(book)
        elif rating == "dislike":
            self.like.discard(book)
            self.dislike.add(book)
        elif rating == "unknown":
            self.like.discard(book)
            self.dislike.discard(book)
        else:
            raise ValueError(f"I am not smart enough to understand this rating yet.")


    # If you like two books, a book connected to these 2 books gets a higher score.     
    def candidate_scores(self):
        scores: dict[str, float] = {}

        for like in self.taste_profile():
            for neighbor, weight in self.graph.get(like, {}).items():
                if neighbor in self.blocked():
                    continue
                scores[neighbor] = scores.get(neighbor, 0) + weight #Weight to add additional weight to two common books being present
        
        # I need a seed multiplier here to prioritize seeds over non_seeds
        if self.seed_book:
            for neighbor, weight in self.graph.get(self.seed_book, {}).items():
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
                if self.seed_book:
                    scores[neighbor] = scores.get(neighbor, 0) + weight * seed_weight

                
        ranked = sorted(scores.items(), key=lambda x: (-x[1], x[0]))
        return ranked

    def next_book(self):
        #First take the seed's immediate neighbor into account
        if self.seed_book and len(self.seen) == 1:  # only seed shown so far
            neighbors = [(n, w) for n, w in self.graph.get(self.seed_book, {}).items() if n not in self.blocked()]
            if neighbors:
                neighbors.sort(key=lambda x: (-x[1], x[0]))
                book = neighbors[0][0]
                self.seen.add(book)
                return book
        ranked = self.candidate_scores()
        if not ranked:
            return None
        book, score = ranked[0]
        self.seen.add(book)
        return book

    # If candidate scores empty or no new book returned, print "Done"

    def random_unseen(self):
        unseen = [book for book in self.graph if book not in self.seen]
        if not unseen:
            return None
        else:
            book = random.choice(unseen)
            self.seen.add(book)
            return book

