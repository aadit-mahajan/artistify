from dotenv import load_dotenv
import os
import requests
import base64
import json
import logging
from requests.adapters import HTTPAdapter, Retry

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s", filename='debug.log', filemode='w')
logger = logging.getLogger(__name__)

load_dotenv()

client_id = os.getenv("SPOTIFY_CLIENT_ID")
client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

def get_access_token(session):
    auth_string = client_id + ":" + client_secret
    auth_bytes = auth_string.encode("utf-8")
    auth_b64 = str(base64.b64encode(auth_bytes), "utf-8")

    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": "Basic " + auth_b64,
        "Content-Type": "application/x-www-form-urlencoded"
    }

    data = {
        "grant_type": "client_credentials"
    }
    results = session.post(url, headers=headers, data=data)
    json_data = json.loads(results.content)
    
    if "access_token" in json_data:
        access_token = json_data["access_token"]
        logger.info("Access token retrieved successfully.")
        return access_token
    else:
        logger.error("Failed to retrieve access token.")
        raise Exception("Failed to retrieve access token.")
    
def get_auth_header(token):
    return {"Authorization": "Bearer " + token}

def get_track_data(track_id, token, session):
    url = f'https://api.spotify.com/v1/tracks/{track_id}'
    headers = get_auth_header(token)
    response = session.get(url, headers=headers)
    json_data = json.loads(response.content)
    image_link = json_data["album"]["images"][0]["url"]

    out_data = {
        'image_link': image_link,
        'artist': json_data["artists"][0]["name"],
        'track_name': json_data["name"],
        'id': json_data["id"],
    }
    if "id" in out_data:
        logger.info(f"Track data for track ID {track_id} retrieved successfully.")
        return out_data
    else:
        logger.error(f"Failed to retrieve track data for track ID {track_id}.")

def search_track(track_name, token, session):
    url = 'https://api.spotify.com/v1/search'
    headers = get_auth_header(token)

    query = f"?q={track_name}&type=track&limit=1"
    url += query
    response = session.get(url, headers=headers)
    json_data = json.loads(response.content)
    json_data = json_data["tracks"]["items"][0]
    if json_data:
        track_id = json_data["id"]
        track_name = json_data["name"]
        logger.info(f"Track ID for {track_name} retrieved successfully.")
        return track_id, track_name
    else:
        logger.error(f"Failed to retrieve track ID for {track_name}.")
        raise Exception(f"Failed to retrieve track ID for {track_name}.")


if __name__ == "__main__":

    session = requests.Session()

    retry_strategy = Retry(
    total=5,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET", "POST"],
    backoff_factor=1
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    DEFAULT_TIMEOUT = 10

    # test code
    token = get_access_token(session)
    track_search_term = 'Shape of You'
    track_id, track_name, artist_name = search_track(track_search_term, token, session)
    logger.info(f"Track ID: {track_id}, Track Name: {track_name}, artist_name: {artist_name}")
    data = get_track_data(track_id, token, session)
    print(data)
    print(f"Track ID: {track_id}, Track Name: {track_name}")