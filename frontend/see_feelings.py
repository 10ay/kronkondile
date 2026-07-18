'''
Copied from Taylor Hutchison's GitHub: https://github.com/aibhleog/how-are-you/blob/main/see-feelings.py
'''

from datetime import datetime as dt
import os
from pathlib import Path
from frontend.feelings import FEELINGS_FILE

root = Path(__file__).parent
path = root
#import os, sys

#path = root
#FEELINGS_FILE = os.path.join(path, 'feelings.txt')
# reading in file
df = pd.read_csv(FEELINGS_FILE,sep='\t')
feelings = ['Lovesick', 'Average', 'Silly', 'Happy', 'I Love Everything!']


# converting dates to datetime format
dates = [dt.strptime(df.loc[i,'date'],'%d-%b-%Y') for i in df.index.values]

# pre-setting the length of the plot based on # of points
length = len(df)/20
if length > 20: length = 20 # will revisit when we have >1yrs worth of data
if length < 8: length = 8 # for when you're first starting out

# looking at data
plt.figure(figsize=(length,3.5))
ax = plt.gca() # a quick way to get an axes variable

plt.scatter(dates,df.feel,c=df.feel,cmap='BrBG',s=100,edgecolor='k',rasterized=True) # color-coded

# setting up xaxis
interval = max(1, int(len(df)/5))
ax.xaxis.set_major_formatter(md.DateFormatter('%m/%Y'))
ax.xaxis.set_major_locator(md.DayLocator(interval=interval)) # interval is in days
ax.minorticks_on()

# yaxis
ax.yaxis.set_tick_params(which='minor', left=False, right=False)
ax.set_ylim(-0.25,4.25)
ax.set_yticks([0,1,2,3,4,])
ax.set_yticklabels(feelings)

plt.tight_layout()
plt.savefig(Path.resolve(path)/f"tracker.png")
plt.close()