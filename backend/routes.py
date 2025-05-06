from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from genius_handler import get_artist_top_tracks
from spotify_handler import get_access_token, get_track_data, search_track
from process_storyline import split_into_scenes
from esa import generate_esa_vectors
import numpy as np
from model import ArtistRecommender
from generate_soundtrack import assign_songs_to_scenes
from typing import Optional
from dotenv import load_dotenv
import uvicorn
from pydantic import BaseModel
import requests
import time 
from prometheus_client import start_http_server, Gauge, Counter

import logging
# setting up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s", filename='debug.log', filemode='w')
logger = logging.getLogger(__name__)
load_dotenv()

app = FastAPI() # Create FastAPI instance
# CORS middleware to allow cross-origin requests
# This is important for the frontend to be able to communicate with the backend as both are running on different API endpoints

app.add_middleware(
    CORSMiddleware, 
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics
start_http_server(9090)  # Start Prometheus metrics server on port 9090
request_counter = Counter('request_count', 'Total number of requests')
scene_split_time = Gauge('scene_split_time', 'Time taken to split scenes')
esa_vector_generation_time = Gauge('esa_vector_generation_time', 'Time taken to generate ESA vectors')
story_esa_vector_time = Gauge('story_esa_vector_time', 'Time taken to generate story ESA vector')
artist_recommendation_time = Gauge('artist_recommendation_time', 'Time taken to recommend artist')
top_tracks_retrieval_time = Gauge('top_tracks_retrieval_time', 'Time taken to retrieve top tracks')
top_track_lyrics_extraction_time = Gauge('top_track_lyrics_extraction_time', 'Time taken to extract top track lyrics')
tracks_esa_vector_generation_time = Gauge('tracks_esa_vector_generation_time', 'Time taken to generate ESA vectors for tracks')
song_assignment_time = Gauge('song_assignment_time', 'Time taken to assign songs to scenes')

@app.get("/get_track_data")
def get_track_data_endpoint(track_name: str):
    try:
        # this is the spotify API (requires token)
        session = requests.Session()
        token = get_access_token(session)
        track_id, track_name = search_track(track_name, token, session=session)
        track_data = get_track_data(track_id, token, session=session)
        return JSONResponse(content={"track_data": track_data})
    except Exception as e:
        logger.error(f"Error retrieving track data: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)

class soundtrack_request(BaseModel):
    storyline: str
    artist: Optional[str] = None

@app.post("/generate_soundtrack")
def generate_soundtrack(request: soundtrack_request):
    '''
    This is the main function that generates the soundtrack for the given storyline.
    Performs the following steps:
    1. Splits the storyline into scenes.
    2. Generates ESA vectors for each scene.
    3. Generates ESA vector for the entire story.
    4. Recommends an artist based on the story ESA vector.
    5. Retrieves the top tracks of the recommended artist.
    6. Extracts the lyrics of the top tracks.
    7. Generates ESA vectors for the top tracks.
    8. Assigns the top tracks to the scenes based on similarity.
    9. Returns the assigned tracks and their similarity to the scenes.

    Tracking the time taken for each step using Prometheus metrics.

    Args:
        request (soundtrack_request): The request object containing the storyline and artist name.
    Returns:
        JSONResponse: A JSON response containing the assigned tracks and their similarity to the scenes.
    '''
    storyline = request.storyline
    artist = request.artist

    # Increment the request counter
    request_counter.inc()

    try:
        t1 = time.time()
        scenes = split_into_scenes(storyline)

        t2 = time.time()
        scene_esa_vectors = [np.array(generate_esa_vectors(scene)) for scene in scenes]

        t3 = time.time()
        story_esa_vector = np.mean(scene_esa_vectors, axis=0)

        t4 = time.time()
        if not artist:
            artist_recommender = ArtistRecommender()
            best_artists = artist_recommender.predict(story_esa_vector)
            best_artist = best_artists[0]
        else:
            best_artist = artist

        t5 = time.time()
        top_tracks = get_artist_top_tracks(best_artist, top_n=len(scenes))

        t6 = time.time()
        top_track_names = [track[1] for track in top_tracks]
        top_track_lyrics = []
        for track in top_tracks:
            lyrics = track[2]
            lyrics_start_index = lyrics.lower().find("lyrics")
            if lyrics_start_index != -1:
                lyrics = lyrics[lyrics_start_index + len("lyrics"):].strip()
            top_track_lyrics.append(lyrics)

        t7 = time.time()
        tracks_esa_vectors = [np.array(generate_esa_vectors(lyrics)) for lyrics in top_track_lyrics]

        t8 = time.time()
        assignments, total_similarity, sim_matrix = assign_songs_to_scenes(scene_esa_vectors, tracks_esa_vectors)

        t9 = time.time()
        output_dict = {"Chosen Artist": best_artist}
        for scene_index, track_index in assignments:
            scene_text = scenes[scene_index]
            assigned_song = top_track_names[track_index]
            similarity_to_song = sim_matrix[scene_index, track_index]

            # Fill in the output dictionary for each scene
            output_dict[f"Scene {scene_index+1}"] = {
                "scene_text": scene_text,
                "assigned_song": assigned_song,
                "similarity_to_song": similarity_to_song
            }

        performance_times = {
            "scene_split_time": t2 - t1,
            "esa_vector_generation_time": t3 - t2,
            "story_esa_vector_time": t4 - t3,
            "artist_recommendation_time": t5 - t4,
            "top_tracks_retrieval_time": t6 - t5,
            "top_track_lyrics_extraction_time": t7 - t6,
            "tracks_esa_vector_generation_time": t8 - t7,
            "song_assignment_time": t9 - t8
        }

        # set the performance times to the Prometheus metrics
        scene_split_time.set(performance_times["scene_split_time"])
        esa_vector_generation_time.set(performance_times["esa_vector_generation_time"])
        story_esa_vector_time.set(performance_times["story_esa_vector_time"])
        artist_recommendation_time.set(performance_times["artist_recommendation_time"])
        top_tracks_retrieval_time.set(performance_times["top_tracks_retrieval_time"])
        top_track_lyrics_extraction_time.set(performance_times["top_track_lyrics_extraction_time"])
        tracks_esa_vector_generation_time.set(performance_times["tracks_esa_vector_generation_time"])
        song_assignment_time.set(performance_times["song_assignment_time"])

        logger.info(f"Performance times: {performance_times}")
        return JSONResponse(content=output_dict, status_code=200)

    except Exception as e:
        logger.error(f"Error generating soundtrack: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.get("/")
def root():
    return JSONResponse(content={"message": "Welcome to the Artistify API!"})

if __name__ == "__main__":
    uvicorn.run(app=app, host='0.0.0.0', port=12000, log_level="info")
