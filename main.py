#!/usr/bin/python3.6
import json
import requests
import sqlite3
import os
import pprint
import time
import logging
from tqdm import tqdm
import urllib.parse

logging.basicConfig(filename='app.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s')
logging.warning('This will get logged to a file')

api_key_last_fm = 'EDIT_ME'
rating_threshold_local = (4.5/5)
rating_threshold_last_fm = 0.95
limit_artist_return_last_fm = '5'

#A Function to check if an artist is on my hard drive
def no_artist(artist):
    artist_sql = """
    SELECT artist 
    FROM songs where artist LIKE {0}
    """.format("\""+artist+"\"")

    try:
        cur.execute(artist_sql)
        return len(cur.fetchall())
    except:
        logging.warning(f'{artist} name bad. query {artist_sql} bad')

def fetch_reccomend(url):
    try:
        resp = requests.get(
            url,
            params=q,
            stream=True
        )

        if not resp.status_code // 100 == 2:
            return "Error: Unexpected response {}".format(resp)

        fetch = resp.json()
        
        for recs in fetch.items():
            try:
                for artist_obj in recs[1]['artist']:
                    if float(artist_obj['match']) >= rating_threshold_last_fm: #Modify this value to have the recommendations be more exact.
                        artist_list.update({artist_obj['name']:artist_obj['match']})
            except: 
                return "input is unexpected"

    except requests.exceptions.RequestException as e:
        # A serious problem happened, like an SSLError or InvalidURL
        return "Error: {}".format(e)



# get list of last 3750 (NO LIMIT rn) artists rated over 4.5/5
con = sqlite3.connect('file:/home/david/.config/Clementine-qt5/clementine.db?mode=ro', uri=True)
cur = con.cursor()

songs_sql = """
SELECT DISTINCT artist
FROM songs where rating >= {0}
GROUP BY artist
ORDER BY MAX(lastplayed) DESC
""".format(rating_threshold)

#Get X last songs with over a certain rating.
cur.execute(songs_sql)
results = cur.fetchall()

big_list = []

for row in results:
    big_list.append(row)

artist_list={}

print("Downloading Reccomendations...")
for i in tqdm(big_list):
    q={
    'method': 'artist.getsimilar',
    'artist': i,
    'api_key': api_key_last_fm,
    'format': 'json',
    'limit': limit_artist_return_last_fm,
    'autocorrect': True
    }

    fetch_reccomend('http://ws.audioscrobbler.com/2.0/')
    
filtered_dict={}
print("Finding Undiscovered Reccomendations...")
for returned_recs, how_good in tqdm(artist_list.items()):
    #Use Ignore List
    blocked = False
    with open("ignore.txt", "r") as exc:
        for line in exc:
            #print(line.rstrip("\n\r"), returned_recs)
            if line.rstrip("\n\r") == returned_recs:
                blocked = True

    if blocked is not True:
        if no_artist(returned_recs) == 0:
            filtered_dict.update({returned_recs:how_good})

#Print Results by highest recommendation first
for key, value in sorted(filtered_dict.items(), key=lambda x: x[1], reverse=True): 
    print("{} : {} - https://redacted.ch/torrents.php?releasetype=1&order_by=time&order_way=desc&group_results=1&action=advanced&searchsubmit=1&artistname={}".format(key, value, urllib.parse.quote(key)))
