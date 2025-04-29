import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from scipy.optimize import linear_sum_assignment


def assign_songs_to_scenes(scene_vectors, song_vectors):
    """
    Assigns songs to scenes by maximising the overall cosine similarity using the Hungarian algorithm.

    Parameters:
    -----------
    scene_vectors : list of np.ndarray
        List of semantic vectors representing each scene.
    song_vectors : list of np.ndarray
        List of semantic vectors representing each song.

    Returns:
    --------
    assignments : list of tuples
        List of (scene_index, song_index) assignments.
    total_similarity : float
        Sum of similarities for the optimal assignment.
    sim_matrix : np.ndarray
        The cosine similarity matrix between scenes and songs.
    """
    # Compute cosine similarity between each scene and song
    sim_matrix = cosine_similarity(scene_vectors, song_vectors)

    # Convert similarity matrix to a cost matrix for assignment (Hungarian algorithm minimizes cost)
    cost_matrix = 1 - sim_matrix

    # Solve the assignment problem using the Hungarian algorithm
    row_ind, col_ind = linear_sum_assignment(cost_matrix)

    # Pair each scene with its best-matching song
    assignments = list(zip(row_ind, col_ind))

    # Compute total similarity across all assignments
    total_similarity = sum(sim_matrix[i, j] for i, j in assignments)

    return assignments, total_similarity, sim_matrix


if __name__ == "__main__":
    # Sample scene vectors (e.g., semantic representation of scene "vibes")
    scene_vectors = [
        np.array([1.0, 0.0, 0.0]),  # Scene 1
        np.array([0.9, 0.1, 0.0])   # Scene 2
    ]

    # Sample song vectors (e.g., based on lyrics or mood alignment)
    song_vectors = [
        np.array([1.0, 0.0, 0.0]),  # Song 1 - perfect match for Scene 1
        np.array([0.0, 1.0, 0.0]),  # Song 2 - very different, poor match
        np.array([0.8, 0.2, 0.0])   # Song 3 - decent match for Scene 2
    ]

    # Assign songs to scenes optimally based on semantic similarity
    assignments, total_similarity, sim_matrix = assign_songs_to_scenes(scene_vectors, song_vectors)

    # Display the cosine similarity matrix
    print("Cosine Similarity Matrix (Scenes x Songs):\n")
    print(np.round(sim_matrix, 3))

    # Display the assignment results
    print("\nAssignments (Scene → Song):")
    for scene_idx, song_idx in assignments:
        similarity = sim_matrix[scene_idx, song_idx]
        print(f"  Scene {scene_idx + 1} → Song {song_idx + 1} (Similarity: {similarity:.4f})")

    # Display the total similarity score across all assignments
    print(f"\nTotal Similarity: {total_similarity:.4f}")
