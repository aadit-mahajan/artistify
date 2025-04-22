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

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s", filename='debug.log')

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


def load_corpus(corpus_file="./corpus/corpus.json"):
    try:
        with open(corpus_file, "r") as file:
            corpus_dict = json.load(file)
        logging.info(f"Corpus successfully loaded from {corpus_file}.")
        return corpus_dict
    except Exception as e:
        logging.error(f"Failed to load corpus from {corpus_file}: {e}")
        return {}


def lemmatize_corpus(output_file="./corpus/lemmatized_corpus.json"):
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
    corpus = load_corpus("./corpus/lemmatized_corpus.json")
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
        # print(f"Sentence {i}: {sentences[i]}")
        # print(f"Similarity with previous sentence: {sim}")

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
    # testing story
    story = """In 1981, San Francisco salesman Chris Gardner invests his entire life savings in portable bone-density scanners, which he demonstrates to doctors and pitches as a handy improvement over standard X-rays. 
    The scanners play a vital role in Chris's life. While he can sell most of them, the time lag between the sales and his growing financial demands enrages his wife, 
    Linda, who works as a hotel maid. The economic instability increasingly erodes their marriage, despite caring for Christopher Jr., their soon-to-be 5-year-old son. 
    While Chris tries to sell one of the scanners, he meets Jay Twistle, a lead manager and partner for Dean Witter Reynolds and impresses him by solving a Rubik's Cube during a taxi ride. 
    After Jay leaves, Chris skips out on paying the fare, causing the driver to angrily chase him into a BART station, forcing him onto a train just as it departs. 
    However, Chris's new relationship with Jay earns him an interview to become an intern stockbroker. The day before the interview, Chris grudgingly agrees to paint his apartment 
    for free to postpone eviction by his landlord for late rent. While painting, Chris is greeted by two policemen at his doorstep, who arrest him for failure to pay multiple 
    parking tickets. Chris has to spend the night in jail, complicating his schedule for the interview the next day. Chris narrowly arrives at Dean Witter's office on time, 
    albeit still in shabby, paint-spattered clothes. Despite his appearance, Chris still impresses the interviewers and lands a six-month unpaid internship. 
    He is among 20 interns competing for a paid position as a stockbroker. A possible position at her sister's boyfriend's restaurant tempts Linda to leave for New York. 
    With regret, she leaves Christopher in Chris's care. However, Chris’s financial problems worsen when his already diminished bank account is garnished by the IRS for unpaid income taxes, 
    and his landlord finally evicts him and Christopher. With only $21.33 in his bank account, Chris and Christopher are left homeless and desperate; Chris is able to get food 
    and beds at the local shelter, and eventually scrapes together cash for a motel room, but the locks are then changed when he can't pay on time; he is then forced to live out of 
    the restrooms in local BART stations with his son. Later, Chris finds the scanner that he lost in the station earlier. He sells his blood to pay for repairs and then gets a local 
    physician to purchase it, thereby freeing himself to focus solely on his stockbroker training. Disadvantaged by his limited work hours and knowing that maximizing his client contacts 
    and profits is the only way to earn the broker position, Chris develops several ways to make sales calls more efficiently, including reaching out to potential high-value customers in 
    person, a violation of firm protocol. One sympathetic prospect, Walter Ribbon, a top-level pension fund manager, even takes Chris and Christopher to a San Francisco 49ers game, 
    where Chris befriends some of Mr. Ribbon's friends, who are also potential clients. Regardless of his challenges, Chris never reveals his lowly circumstances to his colleagues, 
    even going so far as to lend one of his supervisors, Mr. Frohm, the last five dollars in his wallet for cab fare. He also studies for and aces the stockbroker license exam. 
    As Chris concludes his last day of internship, he is summoned to a meeting with the partners. Mr. Frohm notes that Chris is wearing a nice shirt, to which Chris explains he thought 
    it appropriate to dress for the occasion on his last day. Mr. Frohm thanks him and says Chris should wear another one the following day, letting Chris know that he has won the coveted 
    full-time position and reimburses Chris for the previous cab ride. Fighting back tears, he shakes hands with the partners, then rushes to Christopher's daycare to embrace him. 
    They walk down a street and joke with each other (and are passed by the real Chris Gardner, in a business suit). An epilogue reveals that Gardner went on to form his own multimillion-dollar
    brokerage firm in 1987, and Gardner sold a minority stake in his brokerage firm in a multi-million-dollar deal in 2006."""

    sentences, esa_vectors = generate_esa_vectors_for_story(story)

    if sentences and esa_vectors:

        scenes = group_sentences_into_scenes(sentences, esa_vectors, similarity_threshold=0.15)

        for i, (scene_text, scene_vector) in enumerate(scenes):
            print(f"\nScene {i + 1}: {scene_text}")
            # print(f"ESA Vector: {scene_vector}")
