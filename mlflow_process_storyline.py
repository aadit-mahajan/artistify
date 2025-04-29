import mlflow
import pandas as pd
import numpy as np
import random
from process_storyline import split_into_scenes
from esa import generate_esa_vectors
from sklearn.metrics.pairwise import cosine_similarity


def compute_average_dissimilarity(scene_embeddings):
    """
    Compute a scalar dissimilarity score between all scenes using cosine similarity.
    The dissimilarity is computed as (1 - cosine_similarity), and the final score is the average.

    Args:
    - scene_embeddings: List of scene embeddings (each scene represented by a vector).

    Returns:
    - average_dissimilarity: A single scalar value representing the average dissimilarity.
    """
    # Compute pairwise cosine similarity between scene embeddings
    similarity_matrix = cosine_similarity(scene_embeddings)

    # Convert similarity to dissimilarity (1 - similarity)
    dissimilarity_matrix = 1 - similarity_matrix

    # We want to ignore the diagonal (self-similarity), so we set it to 0 for the calculation
    np.fill_diagonal(dissimilarity_matrix, 0)

    # Compute the average dissimilarity score
    average_dissimilarity = np.mean(dissimilarity_matrix)

    return average_dissimilarity


def evaluate_split(texts, similarity_threshold, min_scene_length):

    scores = []
    for storyline in texts:
        scenes = split_into_scenes(storyline, similarity_threshold, min_scene_length)
        scene_esa_vectors = [np.array(generate_esa_vectors(scene)) for scene in scenes]
        score = compute_average_dissimilarity(scene_esa_vectors)
        scores.append(score)
    return np.mean(scores)


def main(random_seed=5402, sample_size=100):

    df = pd.read_csv("mpst_full_data.csv")
    texts = df["plot_synopsis"].dropna().tolist()

    random.seed(random_seed)
    texts = random.sample(texts, sample_size)

    similarity_thresholds = [0.5, 0.6, 0.7, 0.8, 0.9]
    min_scene_lengths = [2, 3, 4, 5]

    mlflow.set_experiment("scene_splitting")

    for threshold in similarity_thresholds:
        for min_len in min_scene_lengths:
            with mlflow.start_run(run_name=f"thr_{threshold}_minlen_{min_len}", nested=True) as run:
                score = evaluate_split(texts, similarity_threshold=threshold, min_scene_length=min_len)
                mlflow.log_param("similarity_threshold", threshold)
                mlflow.log_param("min_scene_length", min_len)
                mlflow.log_metric("dissimilarity", score)


if __name__ == "__main__":
    main()
