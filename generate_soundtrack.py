import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from scipy.optimize import linear_sum_assignment


def assign_songs_to_scenes(scene_vectors, song_vectors):
    sim_matrix = cosine_similarity(scene_vectors, song_vectors)
    cost_matrix = 1 - sim_matrix
    row_ind, col_ind = linear_sum_assignment(cost_matrix)
    assignments = list(zip(row_ind, col_ind))
    total_similarity = sum(sim_matrix[i, j] for i, j in assignments)
    return assignments, total_similarity, sim_matrix


if __name__ == "__main__":
    scene_vectors = [
        np.array([1.0, 0.0, 0.0]),  # Scene 1
        np.array([0.9, 0.1, 0.0])   # Scene 2
    ]

    song_vectors = [
        np.array([1.0, 0.0, 0.0]),  # Song 1 - best for both scenes, strongest for Scene 1
        np.array([0.0, 1.0, 0.0]),  # Song 2 - poor match
        np.array([0.8, 0.2, 0.0])   # Song 3 - okay match for Scene 2
    ]

    assignments, total_similarity, sim_matrix = assign_songs_to_scenes(scene_vectors, song_vectors)

    print("Cosine Similarity Matrix (Scenes x Songs):\n")
    print(np.round(sim_matrix, 3))

    print("\nAssignments (Scene → Song):")
    for scene_idx, song_idx in assignments:
        similarity = sim_matrix[scene_idx, song_idx]
        print(f"  Scene {scene_idx + 1} → Song {song_idx + 1} (Similarity: {similarity:.4f})")

    print(f"\nTotal Similarity: {total_similarity:.4f}")
