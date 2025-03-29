import os
import json
import logging
from dotenv import load_dotenv
import argparse
import lyricsgenius

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s", filename='genius_handler.log', filemode='w')
logger = logging.getLogger(__name__)

load_dotenv()
access_token = os.getenv("GENIUS_ACCESS_TOKEN")

def get_lyrics(artist, song_name):
    
    genius = lyricsgenius.Genius(
        access_token=access_token,
        excluded_terms=["(Remix)", "(Live)"],
        remove_section_headers=True,
        skip_non_songs=True,
        verbose=False
    )

    song = genius.search_song(title=song_name, artist=artist)
    if not song:
        logger.error(f"Song '{song_name}' by '{artist}' not found.")
        raise Exception(f"Song '{song_name}' by '{artist}' not found.")

    if song:
        lyrics = song.lyrics
        logger.info(f"Lyrics for {song_name} retrieved successfully.")
        return lyrics
    else:
        logger.error(f"Failed to retrieve lyrics for {song_name}.")
        raise Exception(f"Failed to retrieve lyrics for {song_name}.")

def main():
    parser = argparse.ArgumentParser(description="Get lyrics for a song by an artist.")
    parser.add_argument("-a", type=str, help="Artist name")
    parser.add_argument("-s", type=str, help="Song name")
    args = parser.parse_args()

    artist = args.a
    song_name = args.s

    try:
        lyrics = get_lyrics(artist, song_name)
        print(lyrics)
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        print(f"Error: {e}")

if __name__ == "__main__":
    main()