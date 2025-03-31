from fastapi import FastAPI
from fastapi.responses import JSONResponse
from genius_handler import get_lyrics
from spotify_handler import get_artist_top_tracks, get_access_token, get_all_tracks, get_artist_id
from dotenv import load_dotenv
import uvicorn

import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s", filename='routes.log', filemode='w')
logger = logging.getLogger(__name__)
load_dotenv()

app = FastAPI()

@app.get("/get_top_tracks")
def get_top_tracks_endpoint(artist_name: str):
    try:
        token = get_access_token()
        top_tracks = get_artist_top_tracks(token, artist_name)
        return JSONResponse(content={"top_tracks": top_tracks})
    except Exception as e:
        logger.error(f"Error retrieving top tracks: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.get("/get_lyrics")
def get_lyrics_endpoint(artist: str, track_name: str):
    try:
        # this is the genius API (doesnt require token)
        lyrics = get_lyrics(artist, track_name)
        return JSONResponse(content={"lyrics": lyrics})
    except Exception as e:
        logger.error(f"Error retrieving lyrics: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)
    
@app.get("/get_all_tracks_lyrics")
def get_all_tracks_endpoint(artist_name: str):
    try:
        token = get_access_token()
        artist_id, artist_name = get_artist_id(token, artist_name)
        all_tracks = get_all_tracks(artist_id, token)
        all_tracks_lyrics = []
        for track in all_tracks:
            track_name = track["name"]
            lyrics = get_lyrics(artist_name, track_name)
            all_tracks_lyrics.append({"track_name": track_name, "lyrics": lyrics})
        return JSONResponse(content={"all_tracks_lyrics": all_tracks_lyrics})
    except Exception as e:
        logger.error(f"Error retrieving all tracks lyrics: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)
    
@app.get("/")
def root():
    return JSONResponse(content={"message": "In the first age, in the first battle, When the shadows first lengthened, one stood; He chose the path of perpetual torment; In his ravenous hatred he found no peace, and with boiling blood he scoured the Umbral Plains; Seeking vengeance against the dark lords who had wronged him and those that tasted the bite of his sword named him The Doom Slayer"})

if __name__ == "__main__":
    uvicorn.run(app=app, host='0.0.0.0', port=6969, log_level="info")
