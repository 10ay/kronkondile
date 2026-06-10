'''
From Taylor Hutchison's how-are-you script: https://github.com/aibhleog/how-are-you/blob/main/how-are-you.py
'''

import os
import sys
from datetime import datetime as dt
from pathlib import Path

import pandas as pd

root = Path(__file__).parent
FEELINGS_FILE = os.path.join(root, 'feelings.txt')

FEELING_LABELS = {
    0: "bad",
    1: "not the best",
    2: "neutral",
    3: "satisfactory",
    4: "good!",
}


def today_string():
    return dt.strftime(dt.now(), '%d-%b-%Y')


def already_logged_today():
    if not os.path.exists(FEELINGS_FILE) or os.path.getsize(FEELINGS_FILE) == 0:
        return False

    tail = os.popen(f'tail {FEELINGS_FILE}').read()
    lastdate = tail.split('\n')[-2].split('\t')[1]
    return lastdate == today_string()


def log_feeling(feel, date=None):
    """Append a mood entry to feelings.txt."""
    if date is None:
        date = today_string()

    if not os.path.exists(FEELINGS_FILE):
        os.system(f'touch {FEELINGS_FILE}')
        df = pd.read_csv(FEELINGS_FILE, sep='\t', names=['feel', 'date'])
    else:
        df = pd.read_csv(FEELINGS_FILE, sep='\t')

    df.loc[len(df)] = [feel, date]
    df.to_csv(FEELINGS_FILE, sep='\t', index=False)


def run_daily_prompt():
    """Terminal prompt: ask once per day and log the response."""
    if already_logged_today():
        return

    print('''
===================================================

    How are you feeling, today?  Choose 0-4:

    0 : bad
    1 : not the best
    2 : neutral
    3 : satisfactory
    4 : good!

===================================================
    ''')

    feel = input('Response:  ')
    try:
        feel = int(feel)
    except ValueError:
        print('Need to input an integer from 0-4.')
        feel = input('Response:  ')
        try:
            feel = int(feel)
        except ValueError:
            print('\nKilling script, incorrect entry twice.')
            sys.exit(0)

    print()
    log_feeling(feel)
    os.system("clear")


if __name__ == "__main__":
    run_daily_prompt()
