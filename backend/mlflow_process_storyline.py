import mlflow
import pandas as pd
import numpy as np
import random
from process_storyline import split_into_scenes
from esa import generate_esa_vectors
from sklearn.metrics.pairwise import cosine_similarity


def compute_average_dissimilarity(scene_embeddings):
    """
    Computes the average dissimilarity between all pairs of scene embeddings.

    Dissimilarity is defined as (1 - cosine similarity), and self-similarity is excluded.

    Parameters:
    -----------
    scene_embeddings : list of np.ndarray
        A list of ESA-based semantic vectors representing each scene.

    Returns:
    --------
    float
        The average pairwise dissimilarity score across all scenes.
    """
    # Compute pairwise cosine similarity matrix
    similarity_matrix = cosine_similarity(scene_embeddings)

    # Convert to dissimilarity matrix
    dissimilarity_matrix = 1 - similarity_matrix

    # Ignore self-comparisons (diagonal) for averaging
    np.fill_diagonal(dissimilarity_matrix, 0)

    return np.mean(dissimilarity_matrix)


def evaluate_split(texts, similarity_threshold, min_scene_length):
    """
    Evaluates how well a similarity-based scene-splitting configuration performs.

    Parameters:
    -----------
    texts : list of str
        Plot synopses to split and evaluate.
    similarity_threshold : float
        Threshold for determining scene boundaries during splitting.
    min_scene_length : int
        Minimum allowed length (in sentences) of a scene.

    Returns:
    --------
    float
        Average dissimilarity score across all storylines, indicating how distinct the resulting scenes are.
    """
    scores = []

    for storyline in texts:
        # Split each storyline into scenes
        scenes = split_into_scenes(storyline, similarity_threshold, min_scene_length)

        # Convert each scene into its ESA vector representation
        scene_esa_vectors = [np.array(generate_esa_vectors(scene)) for scene in scenes]

        # Score the diversity between scenes
        score = compute_average_dissimilarity(scene_esa_vectors)
        scores.append(score)

    return np.mean(scores)


def main(random_seed=5402, sample_size=100):
    """
    Main function to experiment with different scene splitting parameters and log results to MLflow.

    Parameters:
    -----------
    random_seed : int
        Seed for reproducibility when sampling stories.
    sample_size : int
        Number of storylines to use in the evaluation.
    """
    # Load and sample storyline dataset
    df = pd.read_csv("mpst_full_data.csv")
    texts = df["plot_synopsis"].dropna().tolist()

    random.seed(random_seed)
    texts = random.sample(texts, sample_size)

    # Define the range of parameters to test
    similarity_thresholds = [0.5, 0.6, 0.7, 0.8, 0.9]
    min_scene_lengths = [2, 3, 4, 5]

    # Set up MLflow experiment for tracking
    mlflow.set_experiment("scene_splitting")

    for threshold in similarity_thresholds:
        for min_len in min_scene_lengths:
            with mlflow.start_run(run_name=f"thr_{threshold}_minlen_{min_len}", nested=True) as run:
                # Evaluate the dissimilarity score for this parameter combo
                score = evaluate_split(texts, similarity_threshold=threshold, min_scene_length=min_len)

                # Log experiment parameters and result
                mlflow.log_param("similarity_threshold", threshold)
                mlflow.log_param("min_scene_length", min_len)
                mlflow.log_metric("dissimilarity", score)


if __name__ == "__main__":
    main()
