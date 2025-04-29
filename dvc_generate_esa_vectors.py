# generate_esa_vectors.py
import pandas as pd
import numpy as np
import multiprocessing
import logging
from esa import generate_esa_vectors
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def process_row(row):
    artist, track, lyrics = row
    try:
        esa_vector = generate_esa_vectors(lyrics)
        if esa_vector:
            return artist, track, lyrics, np.array(esa_vector).reshape(1, -1).tolist()
    except Exception as e:
        logging.error(f"ESA error for {artist} - {track}: {e}", exc_info=True)
    return None


if __name__ == "__main__":
    df = pd.read_csv('scraped_artist_data.csv')
    rows = list(zip(df['artist'], df['track'], df['lyrics'].astype(str)))

    with multiprocessing.Pool(processes=multiprocessing.cpu_count()) as pool:
        esa_vectors = pool.map(process_row, rows)

    esa_vectors = [vec for vec in esa_vectors if vec is not None]

    if esa_vectors:
        esa_df = pd.DataFrame(esa_vectors, columns=['artist', 'track', 'lyrics', 'esa_vector'])
        esa_df.to_csv('scraped_esa_vectors_all_lyrics.csv', index=False, mode='w', header=True)

        metrics = {
            "artists_processed": len(esa_df['artist'].unique()),
            "tracks_processed": len(esa_df),
            "esa_vectors_generated": len(esa_vectors)
        }

        with open('metrics.json', 'w') as f:
            json.dump(metrics, f)
