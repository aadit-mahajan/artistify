# fetch_artist_lyrics.py

import pandas as pd
import logging
from genius_handler import get_artist_top_tracks


def generate_artists_corpus(artists_file):
    """
    Generates a DataFrame containing the top tracks and lyrics for a list of artists.

    Parameters:
    -----------
    artists_file : str
        Path to a text file containing artist names, one per line.

    Returns:
    --------
    pd.DataFrame
        A DataFrame with columns: 'artist', 'track', and 'lyrics' for the top tracks of each artist.
    """
    collected_df = pd.DataFrame(columns=['artist', 'track', 'lyrics'])

    # Read artist names from the file
    with open(artists_file, 'r') as f:
        artists = f.read().splitlines()

    # For each artist, fetch their top tracks and lyrics
    for artist in artists:
        try:
            top_tracks = get_artist_top_tracks(artist_name=artist, top_n=10)
            if top_tracks:
                for track in top_tracks:
                    # Append each track's details to the main DataFrame
                    collected_df = pd.concat(
                        [collected_df, pd.DataFrame([track], columns=['artist', 'track', 'lyrics'])],
                        ignore_index=True
                    )
            else:
                logging.warning(f"No top tracks found for {artist}")
        except Exception as e:
            logging.error(f"Error occurred while processing artist '{artist}': {e}", exc_info=True)

    return collected_df


if __name__ == "__main__":
    # Run the corpus generation and save the results to a CSV
    df = generate_artists_corpus('scraped_artists.txt')
    df.to_csv('scraped_artist_data.csv', index=False)
