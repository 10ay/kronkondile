"""

This package logs your feelings and pulls up music recommendations for your music on Youtube.
It is based on my music taste and the music I like to listen to.
The name of this package is based on a star I found and a Mummy Joe's video my ex sent me.

"""

import subprocess, sys
from pathlib import Path
from recommend import format_recommendations, get_recommendations, get_feeling

root = Path(__file__).parent

def run_feelings():
    subprocess.run([sys.executable, str(root / "feelings.py")], check=False)

def main():
    run_feelings()
    feeling_index, feeling_name = get_feeling()

    if feeling_index is None:
        print("You are an empty, hollow shell of a human. You have no feelings.")
        return
    
    recommendations = get_recommendations()
    print(format_recommendations(recommendations, feeling_name=feeling_name))

if __name__ == "__main__":
    main()
    sys.exit(0)
