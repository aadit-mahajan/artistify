import csv
import ast
import numpy as np
from sklearn.neighbors import NearestNeighbors


def load_artist_esa_vectors(file_path='esa_vectors_all_lyrics.csv'):
    """Load artist ESA vectors from a CSV file."""
    artist_esa_vectors = []
    try:
        with open(file_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                artist = row.get('artist', '')
                esa_vector_str = row.get('esa_vector', '[]')

                try:
                    esa_vector = ast.literal_eval(esa_vector_str)
                except Exception as e:
                    print(f"Error parsing ESA vector for {artist}: {e}")
                    esa_vector = []

                artist_esa_vectors.append({
                    'artist': artist,
                    'esa_vector': esa_vector
                })
        return artist_esa_vectors
    except Exception as e:
        print(f"Error loading artist ESA vectors: {e}")
        return []


def find_nearest_neighbors(text_vector, artist_vectors, n_neighbors=5):
    """Find nearest artist vectors to the given text vector."""
    text_vector = np.array(text_vector)

    # Flatten if necessary
    if text_vector.ndim > 2:
        text_vector = text_vector.reshape(1, -1)
    elif text_vector.ndim == 1:
        text_vector = text_vector.reshape(1, -1)

    artist_vectors = np.array(artist_vectors)

    if artist_vectors.ndim > 2:
        artist_vectors = artist_vectors.reshape(artist_vectors.shape[0], -1)

    model = NearestNeighbors(
        n_neighbors=n_neighbors,
        algorithm='auto',
        metric='cosine'
    )

    model.fit(artist_vectors)
    _, indices = model.kneighbors(text_vector)

    return indices


class ArtistRecommender:
    def __init__(self, artist_esa_vectors_file='esa_vectors_all_lyrics.csv', n_neighbors=5):
        self.n_neighbors = n_neighbors
        self.artist_esa_entries = load_artist_esa_vectors(artist_esa_vectors_file)

        # Separate ESA vectors and artist names
        self.artist_vectors = [entry['esa_vector'] for entry in self.artist_esa_entries]
        self.artist_names = [entry['artist'] for entry in self.artist_esa_entries]

    def predict(self, text_vector, n_neighbors=None):
        if n_neighbors is None:
            n_neighbors = self.n_neighbors

        indices = find_nearest_neighbors(text_vector, self.artist_vectors, n_neighbors * 3)  # Get extra for uniqueness

        # Only return unique artist names
        seen = set()
        unique_artists = []
        for i in indices[0]:
            artist = self.artist_names[i]
            if artist not in seen:
                seen.add(artist)
                unique_artists.append(artist)
            if len(unique_artists) >= self.n_neighbors:
                break

        return unique_artists
