# fetch_artist_lyrics.py
import pandas as pd
import logging
from genius_handler import get_artist_top_tracks


def generate_artists_corpus(artists_file):
    collected_df = pd.DataFrame(columns=['artist', 'track', 'lyrics'])
    with open(artists_file, 'r') as f:
        artists = f.read().splitlines()
    for artist in artists:
        try:
            top_tracks = get_artist_top_tracks(artist_name=artist, top_n=10)
            if top_tracks:
                for track in top_tracks:
                    collected_df = pd.concat(
                        [collected_df, pd.DataFrame([track], columns=['artist', 'track', 'lyrics'])], ignore_index=True)
            else:
                logging.warning(f"No top tracks for {artist}")
        except Exception as e:
            logging.error(f"Error with {artist}: {e}", exc_info=True)
    return collected_df


if __name__ == "__main__":
    df = generate_artists_corpus('scraped_artists.txt')
    df.to_csv('scraped_artist_data.csv', index=False)
