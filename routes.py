from fastapi import FastAPI
from fastapi.responses import JSONResponse
from genius_handler import get_lyrics
from spotify_handler import get_access_token, get_track_data, search_track
from dotenv import load_dotenv
import uvicorn
import requests

import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s", filename='routes.log', filemode='w')
logger = logging.getLogger(__name__)
load_dotenv()

app = FastAPI()

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

@app.get("/generate_soundtrack")
def generate_soundtrack():
   pass  # Placeholder for the generate_soundtrack function
#    this should send the text to the ESA API and get the soundtrack


@app.get("/")
def root():
    return JSONResponse(content={"message": "Welcome to the Artistify API!"})

if __name__ == "__main__":
    uvicorn.run(app=app, host='0.0.0.0', port=12000, log_level="info")
