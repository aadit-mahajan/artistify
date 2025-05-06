import os
import logging
from dotenv import load_dotenv
import lyricsgenius
import re
import concurrent.futures
# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s", filename='debug.log', filemode="w")
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
    '''
    Clean the lyrics by removing unwanted characters and formatting.
    Args:
        lyrics (str): The input lyrics to clean.
    Returns:
        str: The cleaned lyrics.
    '''
    disallowed_chars = re.compile(r"[^a-zA-Z0-9\s.,!?\"\'()\-:;]")
    lyrics = disallowed_chars.sub("", lyrics)
    lyrics = lyrics.replace("\n", " ")
    lyrics = lyrics.replace("\r", " ")
    lyrics = lyrics.strip()
    return lyrics

def get_artist_top_tracks(artist_name, top_n=10):
    '''
    Fetch the top tracks of an artist from Genius and return their lyrics.
    Args:
        artist_name (str): The name of the artist.
        top_n (int): The number of top tracks to fetch.
    Returns:
        list: A list of tuples containing artist name, track name, and lyrics.
    '''

    genius = lyricsgenius.Genius(
        access_token=access_token,
        excluded_terms=["(Remix)", "(Live)"],
        remove_section_headers=True,
        verbose=False, 
        retries=3,
        sleep_time=0.2, 
        timeout=5
    )                                               # Genius API client

    def get_lyrics(track_name, retries = 3):
        '''
        Helper function to fetch lyrics for a given track name.
        Args:
            track_name (str): The name of the track.
            retries (int): Number of retry attempts.
        Returns:
            list: A list containing artist name, track name, and lyrics.
        '''
        track_name = clean_title(track_name)    # remove unwanted characters
        for attempt in range(retries):  
            track = genius.search_song(title=track_name)    # search for the song
            if track and track.lyrics:
                lyrics = clean_lyrics(track.lyrics)         # clean the lyrics
                return [artist_name, track_name, lyrics]
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
            )   # search for the artist
        
        top_tracks_lyrics = []
        max_workers = min(5, len(artist.songs)) 
        # limit the number of threads to the number of songs
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