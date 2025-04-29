# generate_esa_vectors.py
import pandas as pd
import numpy as np
from pyspark.sql import SparkSession
import multiprocessing
import logging
from esa import generate_esa_vectors
import json


def get_lyrics_partition(partition):
    for artist, track, lyrics in partition:
        try:
            esa_vector = generate_esa_vectors(lyrics)
            if esa_vector:
                yield artist, track, lyrics, np.array(esa_vector).reshape(1, -1).tolist()
        except Exception as e:
            logging.error(f"ESA error: {e}", exc_info=True)


if __name__ == "__main__":
    num_cores = multiprocessing.cpu_count()
    num_partitions = num_cores * 2

    df = pd.read_csv('scraped_artist_data.csv')
    spark = SparkSession.builder.appName("ESA vector generation").getOrCreate()
    sc = spark.sparkContext

    rdd = sc.parallelize(
        list(zip(df['artist'], df['track'], df['lyrics'].astype(str))),
        numSlices=num_partitions
    )

    esa_vectors = rdd.mapPartitions(get_lyrics_partition).collect()
    sc.stop()

    if esa_vectors:
        esa_df = pd.DataFrame(esa_vectors, columns=['artist', 'track', 'lyrics', 'esa_vector'])
        esa_df.to_csv('esa_vectors_all_lyrics.csv', index=False, mode='w', header=True)

        metrics = {
            "artists_processed": len(esa_df['artist'].unique()),
            "tracks_processed": len(esa_df),
            "esa_vectors_generated": len(esa_vectors)
        }

        with open('metrics.json', 'w') as f:
            json.dump(metrics, f)
