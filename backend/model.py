import csv
import ast
import numpy as np
from sklearn.neighbors import NearestNeighbors


def load_artist_esa_vectors(file_path='esa_vectors_all_lyrics.csv'):
    """
    Load ESA vectors for each artist from a CSV file.

    Parameters:
    -----------
    file_path : str
        Path to the CSV file containing artist ESA vectors.

    Returns:
    --------
    list of dict
        Each dict contains 'artist' and their associated 'esa_vector' as a list.
    """
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
    """
    Find the nearest artist vectors to a given text vector using cosine similarity.

    Parameters:
    -----------
    text_vector : np.ndarray
        ESA vector representation of the input text.
    artist_vectors : list of list or np.ndarray
        List of ESA vectors representing artists.
    n_neighbors : int
        Number of nearest neighbours to return.

    Returns:
    --------
    np.ndarray
        Indices of the nearest artist vectors.
    """
    text_vector = np.array(text_vector)

    # Reshape the vector to 2D if necessary
    if text_vector.ndim > 2:
        text_vector = text_vector.reshape(1, -1)
    elif text_vector.ndim == 1:
        text_vector = text_vector.reshape(1, -1)

    artist_vectors = np.array(artist_vectors)

    if artist_vectors.ndim > 2:
        artist_vectors = artist_vectors.reshape(artist_vectors.shape[0], -1)

    # Use cosine distance to find nearest neighbours
    model = NearestNeighbors(
        n_neighbors=n_neighbors,
        algorithm='auto',
        metric='cosine'
    )
    model.fit(artist_vectors)
    _, indices = model.kneighbors(text_vector)

    return indices


class ArtistRecommender:
    """
    Recommender class to predict similar artists based on ESA vector similarity.
    """

    def __init__(self, artist_esa_vectors_file='esa_vectors_all_lyrics.csv', n_neighbors=5):
        """
        Initialise the recommender by loading artist ESA vectors.

        Parameters:
        -----------
        artist_esa_vectors_file : str
            Path to the CSV file containing artist ESA vectors.
        n_neighbors : int
            Number of unique artist recommendations to return.
        """
        self.n_neighbors = n_neighbors
        self.artist_esa_entries = load_artist_esa_vectors(artist_esa_vectors_file)

        # Separate vectors and names for use in predictions
        self.artist_vectors = [entry['esa_vector'] for entry in self.artist_esa_entries]
        self.artist_names = [entry['artist'] for entry in self.artist_esa_entries]

    def predict(self, text_vector, n_neighbors=None):
        """
        Recommend similar artists based on a given text ESA vector.

        Parameters:
        -----------
        text_vector : np.ndarray or list
            ESA vector of the input text.
        n_neighbors : int, optional
            Number of unique artist recommendations to return (defaults to class setting).

        Returns:
        --------
        list of str
            Names of the most semantically similar artists.
        """
        if n_neighbors is None:
            n_neighbors = self.n_neighbors

        # Retrieve more neighbours than needed to filter out duplicates
        indices = find_nearest_neighbors(text_vector, self.artist_vectors, n_neighbors * 3)

        seen = set()
        unique_artists = []

        # Keep only unique artist names
        for i in indices[0]:
            artist = self.artist_names[i]
            if artist not in seen:
                seen.add(artist)
                unique_artists.append(artist)
            if len(unique_artists) >= self.n_neighbors:
                break

        return unique_artists
