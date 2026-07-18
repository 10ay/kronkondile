'''
From Taylor Hutchison's how-are-you script: https://github.com/aibhleog/how-are-you/blob/main/how-are-you.py
'''

from datetime import datetime as dt
from pathlib import Path
import os, sys
import pandas as pd

root = Path(__file__).parent
path = root
FEELINGS_FILE = os.path.join(path, 'feelings.txt')

# creating date string for today, will look like ex.: 08-Feb-2021
date = dt.strftime(dt.now(),'%d-%b-%Y')

# boolean varible to mark if already run today
ran = False

# first checking file exists (only necessary the first time you run this)
if os.path.exists(FEELINGS_FILE) == False:
    os.system(f'touch {FEELINGS_FILE}') # creates file
    df = pd.read_csv(FEELINGS_FILE, sep='\t', names=['feel','date']) # specifying columns
else:
    # orginally, the df was read in here, but as it grows in size this could slow down 
    # so I wrote this version instead to just get the tail of the dataset every time for the check
    tail = os.popen(f'tail {FEELINGS_FILE}').read() # writing output to tail
    lastdate = tail.split('\n')[-2].split('\t')[1] # accesses the last date
    
    if lastdate == date: ran = True # don't need to read in feelings.txt
    else: df = pd.read_csv(FEELINGS_FILE, sep='\t') # don't need to specify cols as they now exist

# checking if this has already been run today
# if it has, nothing happens
if ran == False:

    # the prompt
    print('''
===================================================
    
    How are you feeling, today?  Choose 0-4:
    
    0 : "Lovesick / I feel unloved, like a kidney stone.
    1 : "Average / You are that penguin heading towards the mountains, 70 kilometeres away.
    2 : "Silly / You are going to talk to your dog about homosexuality and communism.
    3 : "Happy / as happy as a minion around Gru.
    4 : "I Love Everything! / Life is all rainbows and sunshine.
    
===================================================
    ''')

    # asking for response
    feel = input('Response:  ')
    try: feel = int(feel)
    except: 
        print('Need to input an integer from 0-4.')
        feel = input('Response:  ' )
        try: feel = int(feel)
        except: 
            print('\nKilling script, incorrect entry twice.')
            sys.exit(0)
    
    print() # just for spacing
        

    # logging answer in table
    # -----------------------

    # appending today's answer to table
    filler_row = [feel,date]
    df.loc[len(df)] = filler_row # adds new row with info for each column

    # saving file
    df.to_csv(FEELINGS_FILE, sep='\t', index=False)

    os.system("clear") # clears terminal, to make it as if it was never there

feelings_dictionary = {    
    0 : "Lovesick / I feel unloved, like a kidney stone.",
    1 : "Average / You are that penguin heading towards the mountains, 70 kilometeres away.",
    2 : "Silly / You are going to talk to your dog about homosexuality and communism.",
    3 : "Happy / as happy as a minion around Gru.",
    4 : "I Love Everything! / Life is all rainbows and sunshine."}
