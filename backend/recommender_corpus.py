import os
import logging
import requests
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
from pyspark.sql import SparkSession
import multiprocessing
from genius_handler import get_artist_top_tracks
from esa import generate_esa_vectors

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', filename='debug.log', filemode='w')
logger = logging.getLogger(__name__)

# Determine optimal number of partitions
num_cores = multiprocessing.cpu_count()
num_partitions = num_cores * 2
logger.info(f"Number of CPU cores: {num_cores}")
logger.info(f"Number of partitions: {num_partitions}")

def scrape_billboard_100_artists():
    url = 'https://www.billboard.com/charts/artist-100/'
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        artist_elements = soup.select('h3.c-title.a-no-trucate.a-font-primary-bold-s')
        artists = [artist.get_text(strip=True) for artist in artist_elements]
        logger.info(f"Found {len(artists)} artists on Billboard.")
        return list(set(artists))
    except Exception as e:
        logger.error(f"Error scraping Billboard: {e}")
        return []

def get_new_artists(scraped, filepath='artists.txt'):
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            existing = f.read().splitlines()
        return list(set(scraped) - set(existing))
    return scraped

def save_artists_to_file(artists, filepath='artists.txt'):
    with open(filepath, 'a' if os.path.exists(filepath) else 'w') as f:
        f.write('\n'.join(artists) + '\n')
    logger.info(f"Saved {len(artists)} new artists to {filepath}")

def generate_artists_corpus(artists):
    collected_df = pd.DataFrame(columns=['artist', 'track', 'lyrics'])
    for artist in artists:
        try:
            top_tracks = get_artist_top_tracks(artist_name=artist, top_n=10)
            if not top_tracks:
                logger.warning(f"No top tracks for {artist}")
                continue
            for track in top_tracks:
                collected_df = pd.concat([collected_df, pd.DataFrame([track], columns=['artist', 'track', 'lyrics'])], ignore_index=True)
            logger.info(f"Processed artist: {artist}")
        except Exception as e:
            logger.error(f"Error processing artist {artist}: {e}", exc_info=True)
    return collected_df

def get_lyrics_partition(partition):
    for artist, track, lyrics in partition:
        try:
            esa_vector = generate_esa_vectors(lyrics)
            if esa_vector:
                yield (artist, track, lyrics, np.array(esa_vector).reshape(1, -1).tolist())
            else:
                logger.warning(f"Empty ESA vector for {artist} - {track}")
        except Exception as e:
            logger.error(f"ESA error for {artist} - {track}: {e}", exc_info=True)

def remove_existing_tracks(new_df, existing_file='esa_vectors_all_lyrics.csv'):
    if not os.path.exists(existing_file):
        return new_df
    existing = pd.read_csv(existing_file, usecols=['artist', 'track'])
    before = len(new_df)
    filtered_df = new_df.merge(existing, on=['artist', 'track'], how='left', indicator=True)
    new_only = filtered_df[filtered_df['_merge'] == 'left_only'].drop(columns=['_merge'])
    logger.info(f"Removed {before - len(new_only)} already processed track(s).")
    return new_only

def main():
    scraped_artists = scrape_billboard_100_artists()
    new_artists = get_new_artists(scraped_artists)

    if not new_artists:
        logger.info("No new artists to process.")
        return

    save_artists_to_file(new_artists)
    new_artist_data = generate_artists_corpus(new_artists)
    if new_artist_data.empty:
        logger.warning("No lyrics fetched for new artists.")
        return

    new_artist_data = remove_existing_tracks(new_artist_data)

    if new_artist_data.empty:
        logger.info("All fetched tracks already exist in ESA vector file.")
        return

    spark = SparkSession.builder.appName("ESA vector generation").getOrCreate()
    sc = spark.sparkContext

    rdd_input = sc.parallelize(
        list(zip(new_artist_data['artist'], new_artist_data['track'], new_artist_data['lyrics'].astype(str))),
        numSlices=num_partitions
    )
    esa_vectors = rdd_input.mapPartitions(get_lyrics_partition).collect()
    sc.stop()

    if esa_vectors:
        esa_df = pd.DataFrame(esa_vectors, columns=['artist', 'track', 'lyrics', 'esa_vector'])
        mode = 'a' if os.path.exists('esa_vectors_all_lyrics.csv') else 'w'
        header = not os.path.exists('esa_vectors_all_lyrics.csv')
        esa_df.to_csv('esa_vectors_all_lyrics.csv', index=False, mode=mode, header=header)
        logger.info("ESA vectors appended to esa_vectors_all_lyrics.csv.")
    else:
        logger.warning("No ESA vectors generated for new artists.")

if __name__ == "__main__":
    main()
