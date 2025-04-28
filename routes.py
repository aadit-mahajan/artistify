from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from genius_handler import get_artist_top_tracks, get_lyrics
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

import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s", filename='routes.log', filemode='w')
logger = logging.getLogger(__name__)
load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware, 
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/get_lyrics")
def get_lyrics_endpoint(artist: str, track_name: str):
    try:
        # this is the genius API (doesnt require token)
        lyrics = get_lyrics(artist, track_name)
        return JSONResponse(content={"lyrics": lyrics})
    except Exception as e:
        logger.error(f"Error retrieving lyrics: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)

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
    storyline = request.storyline
    artist = request.artist

    try:
        scenes = split_into_scenes(storyline)
        scene_esa_vectors = [np.array(generate_esa_vectors(scene)) for scene in scenes]
        story_esa_vector = np.mean(scene_esa_vectors, axis=0)

        if not artist:
            artist_recommender = ArtistRecommender()
            best_artists = artist_recommender.predict(story_esa_vector)
            best_artist = best_artists[0]
        else:
            best_artist = artist

        top_tracks = get_artist_top_tracks(best_artist, top_n=len(scenes))
        top_track_names = [track[1] for track in top_tracks]
        top_track_lyrics = []
        for track in top_tracks:
            lyrics = track[2]
            lyrics_start_index = lyrics.lower().find("lyrics")
            if lyrics_start_index != -1:
                lyrics = lyrics[lyrics_start_index + len("lyrics"):].strip()
            top_track_lyrics.append(lyrics)

        tracks_esa_vectors = [np.array(generate_esa_vectors(lyrics)) for lyrics in top_track_lyrics]

        assignments, total_similarity, sim_matrix = assign_songs_to_scenes(scene_esa_vectors, tracks_esa_vectors)

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

        return JSONResponse(content=output_dict)

    except Exception as e:
        logger.error(f"Error generating soundtrack: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.get("/")
def root():
    return JSONResponse(content={"message": "Welcome to the Artistify API!"})

if __name__ == "__main__":
    uvicorn.run(app=app, host='0.0.0.0', port=12000, log_level="info")
