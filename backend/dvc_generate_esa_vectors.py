# generate_esa_vectors.py

import pandas as pd
import numpy as np
import multiprocessing
import logging
from esa import generate_esa_vectors
import json

# Set up logging configuration to capture timestamps, log level, and messages
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def process_row(row):
    """
    Processes a single (artist, track, lyrics) tuple to generate an ESA vector.

    Parameters:
    -----------
    row : tuple
        A tuple containing (artist, track, lyrics).

    Returns:
    --------
    tuple or None
        A tuple of (artist, track, lyrics, esa_vector) if successful, else None.
    """
    artist, track, lyrics = row
    try:
        esa_vector = generate_esa_vectors(lyrics)
        if esa_vector:
            # Convert the ESA vector to a 2D list format for saving
            return artist, track, lyrics, np.array(esa_vector).reshape(1, -1).tolist()
    except Exception as e:
        logging.error(f"ESA error for {artist} - {track}: {e}", exc_info=True)
    return None


if __name__ == "__main__":
    # Load the scraped artist track and lyrics data
    df = pd.read_csv('scraped_artist_data.csv')

    # Prepare a list of (artist, track, lyrics) tuples
    rows = list(zip(df['artist'], df['track'], df['lyrics'].astype(str)))

    # Use multiprocessing to speed up ESA vector generation
    with multiprocessing.Pool(processes=multiprocessing.cpu_count()) as pool:
        esa_vectors = pool.map(process_row, rows)

    # Filter out rows that failed to generate ESA vectors
    esa_vectors = [vec for vec in esa_vectors if vec is not None]

    if esa_vectors:
        # Save ESA vectors to a CSV
        esa_df = pd.DataFrame(esa_vectors, columns=['artist', 'track', 'lyrics', 'esa_vector'])
        esa_df.to_csv('scraped_esa_vectors_all_lyrics.csv', index=False, mode='w', header=True)

        # Write basic metrics to a JSON file for monitoring
        metrics = {
            "artists_processed": len(esa_df['artist'].unique()),
            "tracks_processed": len(esa_df),
            "esa_vectors_generated": len(esa_vectors)
        }

        with open('metrics.json', 'w') as f:
            json.dump(metrics, f)
