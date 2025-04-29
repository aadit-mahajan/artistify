import json
import logging
import pandas as pd
import numpy as np
import re
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import sent_tokenize, word_tokenize
from sklearn.metrics.pairwise import cosine_similarity
# from genius_handler import get_lyrics
import wikipediaapi
from nltk.corpus import stopwords

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s", filename="debug.log")
logger = logging.getLogger(__name__)

# def load_lyrics(artist_name, track_name):
#     lyrics = get_lyrics(artist=artist_name, track_name=track_name)
#     if not lyrics:
#         logging.error(f"Lyrics not found for {artist_name} - {track_name}.")
#         return None
#     return lyrics

def preprocess_text(text):
    import nltk
    from nltk.tokenize import word_tokenize
    from nltk.corpus import stopwords
    from nltk.stem import WordNetLemmatizer

    nltk.data.path.append("./nltk_data")

    if not text:
        return ""

    tokens = word_tokenize(text.lower())
    tokens = [word for word in tokens if word.isalnum()]
    tokens = [word for word in tokens if word not in stopwords.words("english")]
    
    lemmatizer = WordNetLemmatizer()
    tokens = [lemmatizer.lemmatize(word) for word in tokens]
    
    return " ".join(tokens)  # Return as a string

def clean_text(text):
    text = re.sub(r"\W+", " ", text.lower())
    text = re.sub(r"\s+", " ", text).strip()
    return text

def create_and_save_corpus(topics_file="topics.csv", output_dir="corpus", force_recreate=False):
    logger.info("Starting the process to create and save the corpus.")
    output_file = os.path.join(output_dir, "corpus.json")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        logger.info(f"Output directory {output_dir} created.")
    else:
        logger.info(f"Output directory {output_dir} already exists.")
    logger.info(f"Output file will be saved to {output_file}.")
    print(f"Output file will be saved to {output_file}.")

    if force_recreate:
        logger.info("Force recreate is enabled. Deleting existing corpus file.")
        if os.path.exists(output_file):
            os.remove(output_file)

    if os.path.exists(output_file):
        logger.info(f"Corpus file {output_file} already exists. Loading existing corpus.")
        print("Corpus file already exists. Loading existing corpus.")
        return None
    
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
            text = clean_text(page.summary) 
            corpus_dict[topic] = text
            logger.info(f"Page for {topic} found and added to the corpus.")
        else:
            logger.warning(f"Page for {topic} does not exist.")
    
    try:
        with open(output_file, "w") as file:
            json.dump(corpus_dict, file)
        logger.info(f"Corpus successfully saved to {output_file}.")
    except Exception as e:
        logger.error(f"Failed to save corpus to {output_file}: {e}")

def load_corpus(corpus_file="corpus/corpus.json"):
    try:
        with open(corpus_file, "r") as file:
            corpus_dict = json.load(file)
        logger.info(f"Corpus successfully loaded from {corpus_file}.")
        return corpus_dict
    except Exception as e:
        logger.error(f"Failed to load corpus from {corpus_file}: {e}")
        return {}

def lemmatize_corpus(output_dir="corpus"):
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "lemmatized_corpus.json")
    logger.info("Starting the lemmatization process.")
    
    corpus_dict = load_corpus()
    lemmatizer = WordNetLemmatizer()

    for topic, text in corpus_dict.items():
        tokens = word_tokenize(text.lower())
        tokens = [word for word in tokens if word.isalnum()]
        tokens = [word for word in tokens if word not in stopwords.words("english")]
        tokens = [lemmatizer.lemmatize(word) for word in tokens]
        corpus_dict[topic] = " ".join(tokens)

    try:
        with open(output_file, "w") as file:
            json.dump(corpus_dict, file, indent=4)
        logger.info(f"Lemmatized corpus successfully saved to {output_file}.")
    except Exception as e:
        logger.error(f"Failed to save lemmatized corpus: {e}")

def generate_esa_vectors(text):
    # logger.info("Generating ESA vectors.")

    # corpus = load_corpus(corpus_file="corpus/lemmatized_corpus.json")
    # if not corpus:
    #     logger.error("Corpus is empty or could not be loaded.")
    #     return None

    # lyrics = preprocess_lyrics(lyrics)
    
    # if not lyrics.strip():
    #     logger.error("Lyrics are empty after preprocessing.")
    #     return None

    # all_text = [lyrics] + list(corpus.values())

    # vectorizer = TfidfVectorizer(stop_words="english")
    # tfidf_mat = vectorizer.fit_transform(all_text)

    # if tfidf_mat.shape[0] <= 1:
    #     logger.error("Not enough documents in TF-IDF matrix to compute ESA vectors.")
    #     return None

    # similarities = cosine_similarity(tfidf_mat[0:1], tfidf_mat[1:])

    # esa_vector = np.zeros(len(corpus))  
    # for i, sim in enumerate(similarities[0]):
    #     esa_vector[i] = sim

    # return esa_vector
    logger.info("Generating ESA vectors for artist.")
    
    corpus = load_corpus('./corpus/lemmatized_corpus.json')
    if not corpus:
        logger.error("Corpus is empty or could not be loaded.")
        return [], []

    sentences = sent_tokenize(text)
    processed_sentences = [preprocess_text(s) for s in sentences]
    processed_corpus = list(corpus.values())
    all_documents = processed_sentences + processed_corpus

    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf_matrix = vectorizer.fit_transform(all_documents)

    esa_vectors = []
    for i in range(len(processed_sentences)):
        similarities = cosine_similarity(tfidf_matrix[i:i+1], tfidf_matrix[len(processed_sentences):])
        esa_vector = similarities.flatten()
        esa_vectors.append(esa_vector)
    
    if esa_vectors:
        esa_vectors = np.mean(esa_vectors, axis=0)
        return esa_vectors.tolist()
    else:
        logger.error("No ESA vectors generated.")
    return []

if __name__ == "__main__":
    create_and_save_corpus()

    lemmatize_corpus()

    lem_corp_path = os.path.join("corpus", "lemmatized_corpus.json")

    lyrics = load_lyrics("Rascal Flatts", "Life is a highway")
    if lyrics:
        esa_vector = generate_esa_vectors(lyrics)
        keys = load_corpus(corpus_file=lem_corp_path).keys()
        if esa_vector is not None:
            for i, key in enumerate(keys):
                print(f"Similarity with {key}: {esa_vector[i]}")
        else:
            logger.error("ESA vector generation failed.")
