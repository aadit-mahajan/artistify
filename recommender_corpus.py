import requests
from bs4 import BeautifulSoup
import json
import logging
import os
from nltk.tokenize import sent_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from spotify_handler import get_artist_top_tracks, get_access_token
from genius_handler import get_lyrics
import pandas as pd
from pyspark.sql import SparkSession
import multiprocessing
import requests
from requests.adapters import HTTPAdapter, Retry

num_cores = multiprocessing.cpu_count()
num_partitions = num_cores * 2

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', filename='debug.log', filemode='w')
logger = logging.getLogger(__name__)
logger.info(f"Number of CPU cores: {num_cores}")
logger.info(f"Number of partitions: {num_partitions}")

def scrape_billboard_100_artists(session):
    url = 'https://www.billboard.com/charts/artist-100/'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = session.get(url, headers=headers)
        
        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all artist entries on the page
        artist_elements = soup.select('h3.c-title.a-no-trucate.a-font-primary-bold-s')
        artists = [artist.get_text(strip=True) for artist in artist_elements]
        print(artists)
        logger.info(f"Found {len(artists)} artists on the Billboard Hot 100 page.")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return []
    
    return list(set(artists))

def preprocess_sentence(sentence):
    import nltk
    from nltk.tokenize import word_tokenize
    from nltk.corpus import stopwords
    from nltk.stem import WordNetLemmatizer

    nltk.data.path.append("./nltk_data")

    tokens = word_tokenize(sentence.lower())
    tokens = [word for word in tokens if word.isalnum()]
    tokens = [word for word in tokens if word not in stopwords.words("english")]
    lemmatizer = WordNetLemmatizer()
    tokens = [lemmatizer.lemmatize(word) for word in tokens]
    return " ".join(tokens)

def generate_artists_corpus(artists, session):
    token = get_access_token(session=session)
    artists_df = pd.DataFrame(columns=['artist', 'track', 'lyrics'])
    for artist in artists:
        try:
            # Get the top tracks for the artist
            top_tracks = get_artist_top_tracks(artist_name=artist, token=token, session=session)
            if not top_tracks:
                logger.error(f"No top tracks found for {artist}.")
                continue
            
            # Get the lyrics for each track
            for track in top_tracks:
                track_name = track['name']
                print(f"Processing track: {track_name}, artist: {artist}")
                lyrics = get_lyrics(artist=artist, track_name=track_name)
                if lyrics:
                    # Preprocess the lyrics
                    processed_lyrics = preprocess_sentence(lyrics)
                    new_row = pd.DataFrame([{'artist': artist, 'track': track_name, 'lyrics': processed_lyrics}])
                    artists_df = pd.concat([artists_df, new_row], ignore_index=True)
                else:
                    logger.error(f"Lyrics not found for {artist} - {track}.")
                    continue

            print(f"Processed artist: {artist}")
            logger.info(f"Processed artist: {artist}")
        except Exception as e:
            logger.error(f"Error processing artist {artist}: {e}", exc_info=True)
            continue
    
        # save artists_df to a csv file
    artists_df.to_csv('artists_data.csv', index=False)
    
    return artists_df

def load_corpus(corpus_file):
    try:
        with open(corpus_file, "r") as file:
            corpus_dict = json.load(file)
        logging.info(f"Corpus successfully loaded from {corpus_file}.")
        return corpus_dict
    except Exception as e:
        logging.error(f"Failed to load corpus from {corpus_file}: {e}")
        return {}
    
def generate_artist_esa_vectors(text):
    logger.info("Generating ESA vectors for artist.")
    
    corpus = load_corpus('./corpus/corpus.json')
    if not corpus:
        logger.error("Corpus is empty or could not be loaded.")
        return [], []
    
    sentences = sent_tokenize(text)
    processed_sentences = [preprocess_sentence(s) for s in sentences]
    processed_corpus = list(corpus.values())
    all_documents = processed_sentences + processed_corpus
    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf_matrix = vectorizer.fit_transform(all_documents)

    esa_vectors = []
    for i in range(len(processed_sentences)):
        similarities = cosine_similarity(tfidf_matrix[i:i+1], tfidf_matrix[len(processed_sentences):])
        esa_vector = similarities.flatten()
        esa_vectors.append(esa_vector)

    return esa_vectors, processed_sentences

def get_lyrics_partition(partition):
    for entry in partition:
        lyrics = entry[2]
        artist = entry[0]
        track = entry[1]
        logger.info(f"Processing lyrics for {artist} - {track}.")
        try:
            esa_vector, _ = generate_artist_esa_vectors(lyrics)
            if not esa_vector:
                logger.error(f"ESA vector generation failed for {entry}.")
                continue
            # Convert the ESA vector to a 2D array
            esa_vector = np.array(esa_vector).reshape(1, -1)
            yield (artist, track, lyrics, esa_vector.tolist())
        except Exception as e:
            logger.error(f"Error processing lyrics {entry}: {e}", exc_info=True)
            continue

if __name__ == "__main__":

    # start a requests session for batch requests to spotify API
    session = requests.Session()

    retry_strategy = Retry(
    total=5,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET", "POST"],
    backoff_factor=1
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    DEFAULT_TIMEOUT = 10

    GENERATE_CORPUS = True

    artists = scrape_billboard_100_artists(session)
    
    # check if the artists.txt file exists
    if os.path.exists('artists.txt'):
        with open('artists.txt', 'r') as f:
            existing_artists = f.read().splitlines()
            artists = list(set(artists) - set(existing_artists))
            if not artists:
                print("No new artists to add.")
                GENERATE_CORPUS = False
            print(f"New artists added: {artists}")

            # update the artists.txt file
            with open('artists.txt', 'a') as f:
                f.write('\n'.join(artists))
                logger.info(f"Artists added to artists.txt: {artists}")
    else:
        with open('artists.txt', 'w') as f:
            f.write('\n'.join(artists))
            logger.info(f"Artists saved to artists.txt: {artists}")
    
    # Generate the artists corpus if required
    if GENERATE_CORPUS:
        artists_df = generate_artists_corpus(artists, session)
    else:
        # Load the artists data from the CSV file
        artists_df = pd.read_csv('artists_data.csv')
        print(f"Loaded {len(artists_df['artist'].unique())} artists from artists_data.csv.")

    logger.info("Initialising spark session for recommender.")
    # Generate ESA vectors for each artist
    logger.info("Generating ESA vectors for each artist.")
    spark = SparkSession.builder.appName("ESA vector generation").getOrCreate()
    sc = spark.sparkContext

    artists_df = spark.read.csv('artists_data.csv', header=True, inferSchema=True).toPandas()
    artists_df['esa_vector'] = None
    artists_df['lyrics'] = artists_df['lyrics'].astype(str)
    esa_rdd = sc.parallelize(
        list(zip(artists_df['artist'], artists_df['track'], artists_df['lyrics'])),
        numSlices=num_partitions
    )
    esa_vectors = esa_rdd.mapPartitions(get_lyrics_partition)
    esa_vectors = esa_vectors.collect()
    # convert to dataframe
    esa_vectors_df = pd.DataFrame(esa_vectors, columns=['artist', 'track', 'lyrics', 'esa_vector'])
    # Save the DataFrame to a CSV file
    esa_vectors_df.to_csv('esa_vectors_all_lyrics.csv', index=False)

    sc.stop()


