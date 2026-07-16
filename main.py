"""

This package logs your feelings and pulls up music recommendations for your music on Youtube.
It is based on my music taste and the music I like to listen to.
The name of this package is based on a star I found and a Mummy Joe's video my ex sent me.

"""

import subprocess, sys
from pathlib import Path
from recommend import format_recommendations, get_recommendations, get_feeling
from discover import main as discover_main
from discover_books import main as discover_books_main
from discover_movies import main as discover_movies_main
from mood_playlist import main as mood_playlist_main

root = Path(__file__).parent

def run_feelings():
    subprocess.run([sys.executable, str(root / "feelings.py")], check=False)

def main():
    run_feelings()
    feeling_index, feeling_name = get_feeling()

    print(f"What would you like to do today?")
    print(f"  [1] A quick music recommendation for your mood")
    print(f"  [2] Discover music and artists based on your mood")
    print(f"  [3] Discover books based on your mood (This is slow because books are slow to call)")
    print(f"  [4] Discover movies based on your mood")
    print(f"  [5] Generate a mood playlist")

    input_choice = input("Response: ").strip().lower()
    
    if input_choice == "1":
        recommendations = get_recommendations()
        print(format_recommendations(recommendations, feeling_name=feeling_name))
    elif input_choice == "2":
        discover_main()
    elif input_choice == "3":
        discover_books_main()
    elif input_choice == "4":
        discover_movies_main()
    elif input_choice == "5":
        mood_playlist_main()
    elif feeling_index is None:
        print("Why do you have no feelings today?")
        return

if __name__ == "__main__":
    main()
    sys.exit(0)
