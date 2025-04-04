import nltk

nltk.download("punkt")
nltk.download("wordnet")
nltk.download("stopwords")

import json
import logging
import pandas as pd
import numpy as np
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from genius_handler import get_lyrics
import wikipediaapi
from nltk.corpus import stopwords

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def load_lyrics(artist_name, track_name):
    lyrics = get_lyrics(artist=artist_name, track_name=track_name)
    if not lyrics:
        logging.error(f"Lyrics not found for {artist_name} - {track_name}.")
        return None
    return lyrics

def preprocess_lyrics(lyrics):
    if not lyrics:
        return ""

    tokens = nltk.word_tokenize(lyrics.lower())
    tokens = [word for word in tokens if word.isalnum()]
    tokens = [word for word in tokens if word not in stopwords.words("english")]
    
    lemmatizer = nltk.WordNetLemmatizer()
    tokens = [lemmatizer.lemmatize(word) for word in tokens]
    
    return " ".join(tokens)  # Return as a string

def clean_text(text):
    text = re.sub(r"\W+", " ", text.lower())
    text = re.sub(r"\s+", " ", text).strip()
    return text

def create_and_save_corpus(topics_file="topics.csv", output_file="corpus.json"):
    logging.info("Starting the process to create and save the corpus.")
    
    wiki = wikipediaapi.Wikipedia(
        user_agent="artistify_wiki_user", 
        language="en", 
        extract_format=wikipediaapi.ExtractFormat.WIKI
    )
    
    topics = pd.read_csv(topics_file)
    wiki_titles = topics["Wikipedia Article"].tolist()
    
    corpus_dict = {}
    for topic in wiki_titles:
        page = wiki.page(topic)
        if page.exists():
            text = clean_text(page.summary)  # Use summary instead of full text
            corpus_dict[topic] = text
            logging.info(f"Page for {topic} found and added to the corpus.")
        else:
            logging.warning(f"Page for {topic} does not exist.")
    
    try:
        with open(output_file, "w") as file:
            json.dump(corpus_dict, file)
        logging.info(f"Corpus successfully saved to {output_file}.")
    except Exception as e:
        logging.error(f"Failed to save corpus to {output_file}: {e}")

def load_corpus(corpus_file="corpus.json"):
    try:
        with open(corpus_file, "r") as file:
            corpus_dict = json.load(file)
        logging.info(f"Corpus successfully loaded from {corpus_file}.")
        return corpus_dict
    except Exception as e:
        logging.error(f"Failed to load corpus from {corpus_file}: {e}")
        return {}

def generate_esa_vectors(lyrics):
    logging.info("Generating ESA vectors.")

    corpus = load_corpus()
    if not corpus:
        logging.error("Corpus is empty or could not be loaded.")
        return None

    lyrics = preprocess_lyrics(lyrics)
    
    if not lyrics.strip():
        logging.error("Lyrics are empty after preprocessing.")
        return None

    all_text = [lyrics] + list(corpus.values())

    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf_mat = vectorizer.fit_transform(all_text)

    if tfidf_mat.shape[0] <= 1:
        logging.error("Not enough documents in TF-IDF matrix to compute ESA vectors.")
        return None

    similarities = cosine_similarity(tfidf_mat[0:1], tfidf_mat[1:])

    esa_vector = np.zeros(len(corpus))  
    for i, sim in enumerate(similarities[0]):
        esa_vector[i] = sim

    return esa_vector

if __name__ == "__main__":
    create_and_save_corpus()

    lyrics = load_lyrics("Michael Jackson", "Thriller")
    if lyrics:
        print(generate_esa_vectors(lyrics))
