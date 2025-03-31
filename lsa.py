from gensim.models import TfidfModel
from gensim.corpora import Dictionary, WikiCorpus
from gensim.similarities import MatrixSimilarity
import nltk
import json
from genius_handler import get_lyrics
from spotify_handler import get_artist_top_songs

def load_lyrics(artist_name):

    

