import os
import logging
from dotenv import load_dotenv
import argparse
import lyricsgenius
import re
# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s", filename='genius_handler.log', filemode='w')
logger = logging.getLogger(__name__)

load_dotenv()
access_token = os.getenv("GENIUS_ACCESS_TOKEN")

def clean_title(title):
    # remove all words in parentheses/brackets
    title = title.split("(")[0]
    title = title.split("[")[0]
    return title.strip()

def clean_lyrics(lyrics):
    disallowed_chars = re.compile(r"[^a-zA-Z0-9\s.,!?\"'()\-:;]")
    lyrics = disallowed_chars.sub("", lyrics)
    lyrics = lyrics.replace("\n", " ")
    lyrics = lyrics.replace("\r", " ")
    lyrics = lyrics.strip()
    return lyrics

def get_lyrics(artist, track_name):
    genius = lyricsgenius.Genius(
        access_token=access_token,
        excluded_terms=["(Remix)", "(Live)"],
        remove_section_headers=True,
        verbose=False, 
        retries=3,
        sleep_time=0.5
    )
    track_name = clean_title(track_name)
    track = genius.search_song(title=track_name, artist=artist)
    if not track:
        logger.error(f"track '{track_name}' by '{artist}' not found. Trying only with track name.")
        track = genius.search_song(title=track_name)

        if not track:
            logger.error(f"track '{track_name}' not found.")
            raise Exception(f"track '{track_name}' not found.")
        else:
            logger.info(f"track '{track_name}' found without artist.")
            track_name = track.title
            artist = track.primary_artist.name
            logger.info(f"Artist for '{track_name}' is '{artist}'.")
            track = genius.search_song(title=track_name, artist=artist)

    if not track:
        logger.error(f"track '{track_name}' not found.")
        return None
    if track:
        lyrics = track.lyrics
        lyrics = clean_lyrics(lyrics)
        logger.info(f"Lyrics for {track_name} retrieved successfully.")
        return lyrics
    else:
        logger.error(f"Failed to retrieve lyrics for {track_name}.")
        raise Exception(f"Failed to retrieve lyrics for {track_name}.")

def main():
    parser = argparse.ArgumentParser(description="Get lyrics for a track by an artist.")
    parser.add_argument("-a", type=str, help="Artist name")
    parser.add_argument("-s", type=str, help="track name")
    args = parser.parse_args()

    artist = args.a
    track_name = args.s

    try:
        lyrics = get_lyrics(artist, track_name)
        print(lyrics)
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        print(f"Error: {e}")

if __name__ == "__main__":
    main()