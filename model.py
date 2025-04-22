from sklearn.neighbors import NearestNeighbors
import json

def find_nearest_neighbors(text_vector, artist_vectors, n_neighbors=5):
    # Convert the text vector to a 2D array
    text_vector = text_vector.reshape(1, -1)
    
    # Ensure artist_vectors is a 2D array
    import numpy as np
    artist_vectors = np.array(artist_vectors)
    if artist_vectors.ndim == 1:
        artist_vectors = artist_vectors.reshape(1, -1)
    
    model = NearestNeighbors(
        n_neighbors=n_neighbors,
        algorithm='auto',
        metric='cosine'
        )
    
    model.fit(artist_vectors)
    distances, indices = model.kneighbors(text_vector)
    
    return distances, indices

def load_artist_esa_vectors(file_path='artist_esa_vectors.json'):
    try:
        with open(file_path, 'r') as f:
            artist_esa_vectors = json.load(f)
        return artist_esa_vectors
    except Exception as e:
        print(f"Error loading artist ESA vectors: {e}")
        return {}
    
class ArtistRecommender:
    def __init__(self, artist_esa_vectors_file='esa_vectors_all_lyrics.csv', n_neighbors=5):
        self.n_neighbors = n_neighbors
        self.artist_esa_vectors = load_artist_esa_vectors(artist_esa_vectors_file)
        self.artist_names = list(self.artist_esa_vectors.keys())
        self.artist_vectors = [vector for vector in self.artist_esa_vectors.values()]
    
    def predict(self, text_vector, n_neighbors=5):
        distances, indices = find_nearest_neighbors(text_vector, self.artist_vectors, n_neighbors)
        recommended_artists = [(self.artist_names[i], distances[0][j]) for j, i in enumerate(indices[0])]
        return recommended_artists
    
