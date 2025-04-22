from dotenv import load_dotenv
import os
import requests
from requests import post, get
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

def get_artist_id(token, artist_name, session):
    url = 'https://api.spotify.com/v1/search'
    headers = get_auth_header(token)

    query = f"?q={artist_name}&type=artist&limit=1"
    url += query
    response = session.get(url, headers=headers)
    json_data = json.loads(response.content)
    json_data = json_data["artists"]["items"][0]
    if json_data:
        artist_id = json_data["id"]
        artist_name = json_data["name"]
        logger.info(f"Artist ID for {artist_name} retrieved successfully.")
        return artist_id, artist_name
    else:
        logger.error(f"Failed to retrieve artist ID for {artist_name}.")
        raise Exception(f"Failed to retrieve artist ID for {artist_name}.")

def get_artist_top_tracks(token, artist_name, session):

    artist_id, artist_name = get_artist_id(token, artist_name, session)
    if not artist_id:
        logger.error(f"Artist ID not found for {artist_name}.")
        raise Exception(f"Artist ID not found for {artist_name}.")
    logger.info(f"Artist ID for {artist_name} is {artist_id}.")

    url = f'https://api.spotify.com/v1/artists/{artist_id}/top-tracks'
    headers = get_auth_header(token)

    response = session.get(url, headers=headers, params={"market": "US"})
    json_data = json.loads(response.content)
    if "tracks" in json_data:
        top_tracks = json_data["tracks"]
        logger.info(f"Top tracks for artist ID {artist_id} retrieved successfully.")
        return top_tracks
    else:
        logger.error(f"Failed to retrieve top tracks for artist ID {artist_id}.")
        raise Exception(f"Failed to retrieve top tracks for artist ID {artist_id}.")

def get_artist_track_ids(artist_id, token, session):
    albums = []
    url = f'https://api.spotify.com/v1/artists/{artist_id}/albums'
    params = {
        "include_groups": "album,single", 
        "limit": 20
    }
    headers = get_auth_header(token)
    response = session.get(url, headers=headers, params=params)
    json_data = json.loads(response.content)
    if "items" in json_data:
        albums = json_data["items"]
        if "next" in json_data and json_data["next"]:
            next_url = json_data["next"]
            while next_url:
                response = session.get(next_url, headers=headers)
                json_data = json.loads(response.content)
                if "items" in json_data:
                    albums += json_data["items"]
                next_url = json_data.get("next")

    track_ids = []
    for album in albums:
        album_id = album["id"]
        tracks = get_album_tracks(album_id, token, session)
        for track in tracks:
            track_ids.append(track["id"])
    return track_ids

def get_album_tracks(album_id, token, session):
    tracks = []
    url = f'https://api.spotify.com/v1/albums/{album_id}/tracks'
    headers = get_auth_header(token)
    response = session.get(url, headers=headers)
    json_data = json.loads(response.content)
    if "items" in json_data:
        tracks = json_data["items"]
        logger.info(f"Tracks for album ID {album_id} retrieved successfully.")
        return tracks
    else:
        logger.error(f"Failed to retrieve tracks for album ID {album_id}.")
        raise Exception(f"Failed to retrieve tracks for album ID {album_id}.")

def get_track_data(track_id, token, session):
    url = f'https://api.spotify.com/v1/tracks/{track_id}'
    headers = get_auth_header(token)
    response = session.get(url, headers=headers)
    json_data = json.loads(response.content)

    if "id" in json_data:
        logger.info(f"Track data for track ID {track_id} retrieved successfully.")
        return json_data
    else:
        logger.error(f"Failed to retrieve track data for track ID {track_id}.")
    
def get_all_tracks(artist_id, token, session, top_n=-1):
    all_tracks = []
    track_ids = get_artist_track_ids(artist_id, token, session)
    for track_id in track_ids:
        track_data = get_track_data(track_id, token, session)
        all_tracks.append(track_data)

    # sort the tracks by popularity
    all_tracks.sort(key=lambda x: x["popularity"], reverse=True)

    logger.info(f"All tracks for artist ID {artist_id} retrieved successfully.")
    return all_tracks[:top_n]

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
    artist_name = "dua lipa"
    artist_id, artist_name = get_artist_id(token, artist_name, session)
    all_tracks = get_all_tracks(artist_id, token, session, top_n=5)
    for track in all_tracks:
        print(f"Track: {track['name']}, Popularity: {track['popularity']}")