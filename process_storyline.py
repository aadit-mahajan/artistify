import nltk

nltk.download("punkt")
nltk.download("wordnet")
nltk.download("stopwords")

import json
import logging
import numpy as np
import re
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def clean_text(text):
    text = re.sub(r"\W+", " ", text.lower())
    text = re.sub(r"\s+", " ", text).strip()
    return text


def preprocess_sentence(sentence):
    tokens = word_tokenize(sentence.lower())
    tokens = [word for word in tokens if word.isalnum()]
    tokens = [word for word in tokens if word not in stopwords.words("english")]
    lemmatizer = WordNetLemmatizer()
    tokens = [lemmatizer.lemmatize(word) for word in tokens]
    return " ".join(tokens)


def load_corpus(corpus_file="corpus.json"):
    try:
        with open(corpus_file, "r") as file:
            corpus_dict = json.load(file)
        logging.info(f"Corpus successfully loaded from {corpus_file}.")
        return corpus_dict
    except Exception as e:
        logging.error(f"Failed to load corpus from {corpus_file}: {e}")
        return {}


def lemmatize_corpus(output_file="lemmatized_corpus.json"):
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
        logging.info(f"Lemmatized corpus successfully saved to {output_file}.")
    except Exception as e:
        logging.error(f"Failed to save lemmatized corpus: {e}")


def generate_esa_vectors_for_story(story):
    logging.info("Generating ESA vectors for story.")
    corpus = load_corpus("lemmatized_corpus.json")
    if not corpus:
        logging.error("Corpus is empty or could not be loaded.")
        return [], []

    sentences = sent_tokenize(story)
    processed_sentences = [preprocess_sentence(s) for s in sentences]
    processed_corpus = list(corpus.values())
    all_documents = processed_sentences + processed_corpus

    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf_mat = vectorizer.fit_transform(all_documents)

    esa_vectors = []
    for i in range(len(processed_sentences)):
        similarities = cosine_similarity(tfidf_mat[i:i+1], tfidf_mat[len(processed_sentences):])
        esa_vector = similarities.flatten()
        esa_vectors.append(esa_vector)

    return sentences, esa_vectors


def group_sentences_into_scenes(sentences, esa_vectors, similarity_threshold=0.15):
    scenes = []
    current_scene = [sentences[0]]
    current_scene_vectors = [esa_vectors[0]]

    for i in range(1, len(sentences)):
        vec1 = esa_vectors[i - 1]
        vec2 = esa_vectors[i]
        sim = cosine_similarity([vec1], [vec2])[0][0]

        if sim >= similarity_threshold:
            current_scene.append(sentences[i])
            current_scene_vectors.append(vec2)
        else:
            scene_text = " ".join(current_scene)
            scene_vector = np.mean(current_scene_vectors, axis=0)
            scenes.append((scene_text, scene_vector))

            current_scene = [sentences[i]]
            current_scene_vectors = [vec2]

    if current_scene:
        scene_text = " ".join(current_scene)
        scene_vector = np.mean(current_scene_vectors, axis=0)
        scenes.append((scene_text, scene_vector))

    return scenes


if __name__ == "__main__":
    story = """Chris Gardner, struggling to make ends meet, is seen desperately trying to sell his bone density 
    scanners to doctors, but no one is buying. His wife, Linda, grows increasingly frustrated with their financial 
    instability and leaves him, taking their son with her. Alone, Chris faces the harsh realities of life, 
    but he refuses to give up on providing a better future for his son. Chris secures an unpaid internship at a 
    prestigious stock brokerage firm, despite not having any formal education in finance. He spends long hours 
    studying while trying to take care of his son, sleeping in shelters, and facing constant rejection. Yet, 
    despite these struggles, he maintains hope and determination, holding onto the belief that one day he will 
    succeed. After enduring months of hardship, Chris is finally offered a full-time position at the firm. His hard 
    work and perseverance pay off as he secures the job, and his life begins to turn around. As he walks out of the 
    office with his son, he smiles, knowing that all the sacrifices were worth it, marking the beginning of a new 
    chapter in his life."""

    sentences, esa_vectors = generate_esa_vectors_for_story(story)

    if sentences and esa_vectors:

        scenes = group_sentences_into_scenes(sentences, esa_vectors, similarity_threshold=0.15)

        for i, (scene_text, scene_vector) in enumerate(scenes):
            print(f"\nScene {i + 1}: {scene_text}")
            # print(f"ESA Vector: {scene_vector}")
