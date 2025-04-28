import os
import logging
from dotenv import load_dotenv
import lyricsgenius
import re
import concurrent.futures
# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s", filename='debug.log')
logger = logging.getLogger(__name__)
import time

load_dotenv()
access_token = os.getenv("GENIUS_ACCESS_TOKEN")

def clean_title(title):
    # remove all words in parentheses/brackets
    title = title.split("(")[0]
    title = title.split("[")[0]
    return title.strip()

def clean_lyrics(lyrics):
    disallowed_chars = re.compile(r"[^a-zA-Z0-9\s.,!?\"\'()\-:;]")
    lyrics = disallowed_chars.sub("", lyrics)
    lyrics = lyrics.replace("\n", " ")
    lyrics = lyrics.replace("\r", " ")
    lyrics = lyrics.strip()
    return lyrics

def get_artist_top_tracks(artist_name, top_n=10):
    genius = lyricsgenius.Genius(
        access_token=access_token,
        excluded_terms=["(Remix)", "(Live)"],
        remove_section_headers=True,
        verbose=False, 
        retries=3,
        sleep_time=0.2, 
        timeout=5
    )

    def get_lyrics(track_name, retries = 3):
        track_name = clean_title(track_name)
        for attempt in range(retries):  
            track = genius.search_song(title=track_name)
            if track and track.lyrics:
                lyrics = clean_lyrics(track.lyrics)
                return lyrics
            else:
                logger.info(f"lyrics not found for track {track_name}: Attempt {attempt}")
        if not track:
            logger.error(f"track '{track_name}' not found.")
            return None
        
            
    try:
        artist = genius.search_artist(
            artist_name=artist_name,
            max_songs=top_n,
            sort="popularity",
            get_full_info=False,
            per_page=top_n
            )
        print(artist.songs)
        top_tracks_lyrics = []
        max_workers = min(5, len(artist.songs)) 
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(get_lyrics, song.title) for song in artist.songs]
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if result:
                    top_tracks_lyrics.append(result)

    except Exception as e:
        logger.error(f"Error retrieving top tracks for {artist_name}: {e}")
        return []
    
    return top_tracks_lyrics

def main():
    artist = 'Dua Lipa'
    t1 = time.time()
    print(get_artist_top_tracks(artist_name=artist))
    t2 = time.time()
    print("process time:", t2-t1)

if __name__ == "__main__":
    main()