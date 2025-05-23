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
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

# Load the Sentence-BERT model for semantic similarity
model = SentenceTransformer('all-MiniLM-L6-v2')

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filename='debug.log'
)


def clean_text(text):
    """
    Remove extra whitespace and newlines from input text.
    """
    return re.sub(r"\s+", " ", text).strip()


def preprocess_sentence(sentence):
    """
    Tokenise, remove stopwords, and lemmatise a sentence.

    Parameters:
    -----------
    sentence : str
        The sentence to process.

    Returns:
    --------
    str
        Preprocessed and lemmatised sentence.
    """
    tokens = word_tokenize(sentence.lower())
    tokens = [word for word in tokens if word.isalnum()]
    tokens = [word for word in tokens if word not in stopwords.words("english")]
    lemmatizer = WordNetLemmatizer()
    tokens = [lemmatizer.lemmatize(word) for word in tokens]
    return " ".join(tokens)


def load_corpus(corpus_file="./corpus/corpus.json"):
    """
    Load a text corpus from a JSON file.

    Parameters:
    -----------
    corpus_file : str
        Path to the JSON corpus file.

    Returns:
    --------
    dict
        Dictionary mapping topics to text content.
    """
    try:
        with open(corpus_file, "r") as file:
            corpus_dict = json.load(file)
        logging.info(f"Corpus successfully loaded from {corpus_file}.")
        return corpus_dict
    except Exception as e:
        logging.error(f"Failed to load corpus from {corpus_file}: {e}")
        return {}


def lemmatize_corpus(output_file="./corpus/lemmatized_corpus.json"):
    """
    Load, preprocess, and lemmatise a text corpus, then save to a JSON file.
    """
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


def split_into_scenes(text, similarity_threshold=0.7, min_scene_length=2):
    """
    Segment a story into scenes based on semantic similarity between adjacent sentences.

    Parameters:
    -----------
    text : str
        The full story or synopsis to segment.
    similarity_threshold : float
        Similarity value below which a scene is split.
    min_scene_length : int
        Minimum number of sentences in a scene before allowing a split.

    Returns:
    --------
    list of str
        List of segmented scenes (as text blocks).
    """
    sentences = sent_tokenize(clean_text(text))
    embeddings = model.encode(sentences)

    scenes = []
    current_scene = [sentences[0]]

    for i in range(1, len(sentences)):
        sim = cosine_similarity([embeddings[i]], [embeddings[i - 1]])[0][0]

        # Start a new scene if similarity drops and scene length is enough
        if sim < similarity_threshold and len(current_scene) >= min_scene_length:
            scenes.append(' '.join(current_scene))
            current_scene = [sentences[i]]
        else:
            current_scene.append(sentences[i])

    if current_scene:
        scenes.append(' '.join(current_scene))

    return scenes


# Optional testing block
if __name__ == "__main__":
    story = """In 1981, San Francisco salesman Chris Gardner invests his entire life savings in portable bone-density 
    scanners, which he demonstrates to doctors and pitches as a handy improvement over standard X-rays. The scanners 
    play a vital role in Chris's life. While he can sell most of them, the time lag between the sales and his growing 
    financial demands enrages his wife, Linda, who works as a hotel maid. The economic instability increasingly 
    erodes their marriage, despite caring for Christopher Jr., their soon-to-be 5-year-old son. While Chris tries to 
    sell one of the scanners, he meets Jay Twistle, a lead manager and partner for Dean Witter Reynolds and impresses 
    him by solving a Rubik's Cube during a taxi ride. After Jay leaves, Chris skips out on paying the fare, 
    causing the driver to angrily chase him into a BART station, forcing him onto a train just as it departs. 
    However, Chris's new relationship with Jay earns him an interview to become an intern stockbroker. The day before 
    the interview, Chris grudgingly agrees to paint his apartment for free to postpone eviction by his landlord for 
    late rent. While painting, Chris is greeted by two policemen at his doorstep, who arrest him for failure to pay 
    multiple parking tickets. Chris has to spend the night in jail, complicating his schedule for the interview the 
    next day. Chris narrowly arrives at Dean Witter's office on time, albeit still in shabby, paint-spattered 
    clothes. Despite his appearance, Chris still impresses the interviewers and lands a six-month unpaid internship. 
    He is among 20 interns competing for a paid position as a stockbroker. A possible position at her sister's 
    boyfriend's restaurant tempts Linda to leave for New York. With regret, she leaves Christopher in Chris's care. 
    However, Chris’s financial problems worsen when his already diminished bank account is garnished by the IRS for 
    unpaid income taxes, and his landlord finally evicts him and Christopher. With only $21.33 in his bank account, 
    Chris and Christopher are left homeless and desperate; Chris is able to get food and beds at the local shelter, 
    and eventually scrapes together cash for a motel room, but the locks are then changed when he can't pay on time; 
    he is then forced to live out of the restrooms in local BART stations with his son. Later, Chris finds the 
    scanner that he lost in the station earlier. He sells his blood to pay for repairs and then gets a local 
    physician to purchase it, thereby freeing himself to focus solely on his stockbroker training. Disadvantaged by 
    his limited work hours and knowing that maximizing his client contacts and profits is the only way to earn the 
    broker position, Chris develops several ways to make sales calls more efficiently, including reaching out to 
    potential high-value customers in person, a violation of firm protocol. One sympathetic prospect, Walter Ribbon, 
    a top-level pension fund manager, even takes Chris and Christopher to a San Francisco 49ers game, where Chris 
    befriends some of Mr. Ribbon's friends, who are also potential clients. Regardless of his challenges, Chris never 
    reveals his lowly circumstances to his colleagues, even going so far as to lend one of his supervisors, 
    Mr. Frohm, the last five dollars in his wallet for cab fare. He also studies for and aces the stockbroker license 
    exam. As Chris concludes his last day of internship, he is summoned to a meeting with the partners. Mr. Frohm 
    notes that Chris is wearing a nice shirt, to which Chris explains he thought it appropriate to dress for the 
    occasion on his last day. Mr. Frohm thanks him and says Chris should wear another one the following day, 
    letting Chris know that he has won the coveted full-time position and reimburses Chris for the previous cab ride. 
    Fighting back tears, he shakes hands with the partners, then rushes to Christopher's daycare to embrace him. They 
    walk down a street and joke with each other (and are passed by the real Chris Gardner, in a business suit). An 
    epilogue reveals that Gardner went on to form his own multimillion-dollar brokerage firm in 1987, and Gardner 
    sold a minority stake in his brokerage firm in a multi-million-dollar deal in 2006."""

    scenes = split_into_scenes(story, similarity_threshold=0.15)

    for i, scene in enumerate(scenes):
        print(f"\nScene {i + 1}:\n{scene}")
