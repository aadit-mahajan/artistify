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
    '''
    Get the access token for Spotify API using client credentials. 
    Make sure to set the environment variables SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET for this to work.
    This function uses the client credentials flow to obtain an access token.
    Args:
        session (requests.Session): The requests session to use for the API call.
    Returns:
        str: The access token.
    '''
    if not client_id or not client_secret:
        logger.error("Client ID or Client Secret not set in environment variables.")
        raise Exception("Client ID or Client Secret not set in environment variables.")
    
    # setup the auth string
    auth_string = client_id + ":" + client_secret   
    auth_bytes = auth_string.encode("utf-8")
    auth_b64 = str(base64.b64encode(auth_bytes), "utf-8")

    # make the request to get the access token
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
    '''
    Helper function to get the authorization header for Spotify API requests.
    '''
    return {"Authorization": "Bearer " + token}

def get_track_data(track_id, token, session):
    '''
    Gets the track data for a given track ID from the Spotify API.
    Args:
        track_id (str): The ID of the track to retrieve data for.
        token (str): The access token for Spotify API.
        session (requests.Session): The requests session to use for the API call.
    Returns:
        dict: A dictionary containing the track data, including image link, artist name, track name, and track ID.
    '''
    # make the request to get the track data
    url = f'https://api.spotify.com/v1/tracks/{track_id}'
    headers = get_auth_header(token)
    response = session.get(url, headers=headers)
    json_data = json.loads(response.content)
    image_link = json_data["album"]["images"][0]["url"]

    # create the output data dictionary
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
    '''
    Search for a track by name using the Spotify API.
    Args:
        track_name (str): The name of the track to search for.
        token (str): The access token for Spotify API.
        session (requests.Session): The requests session to use for the API call.
    Returns:
        tuple: A tuple containing the track ID and track name.
    '''
    # make the request to search for the track
    url = 'https://api.spotify.com/v1/search'
    headers = get_auth_header(token)

    query = f"?q={track_name}&type=track&limit=1"
    url += query
    response = session.get(url, headers=headers)
    json_data = json.loads(response.content)
    json_data = json_data["tracks"]["items"][0]

    # return the track ID and track name
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