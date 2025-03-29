from dotenv import load_dotenv
import os
from requests import post, get
import base64
import json
import logging
import argparse
from genius_handler import get_lyrics

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s", filename='spotify_handler.log', filemode='w')
logger = logging.getLogger(__name__)

load_dotenv()

client_id = os.getenv("SPOTIFY_CLIENT_ID")
client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

def get_access_token():
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
    results = post(url, headers=headers, data=data)
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

def get_artist_id(token, artist_name):
    url = 'https://api.spotify.com/v1/search'
    headers = get_auth_header(token)

    query = f"?q={artist_name}&type=artist&limit=1"
    url += query
    response = get(url, headers=headers)
    json_data = json.loads(response.content)
    json_data = json_data["artists"]["items"][0]
    if json_data:
        artist_id = json_data["id"]
        logger.info(f"Artist ID for {artist_name} retrieved successfully.")
        return artist_id
    else:
        logger.error(f"Failed to retrieve artist ID for {artist_name}.")
        raise Exception(f"Failed to retrieve artist ID for {artist_name}.")

def get_artist_top_songs(token, artist_id):
    url = f'https://api.spotify.com/v1/artists/{artist_id}/top-tracks'
    headers = get_auth_header(token)

    response = get(url, headers=headers, params={"market": "US"})
    json_data = json.loads(response.content)
    if "tracks" in json_data:
        top_songs = json_data["tracks"]
        logger.info(f"Top songs for artist ID {artist_id} retrieved successfully.")
        for song in top_songs:
            print(f"Song: {song['name']}, Popularity: {song['popularity']}")
        return top_songs
    else:
        logger.error(f"Failed to retrieve top songs for artist ID {artist_id}.")
        raise Exception(f"Failed to retrieve top songs for artist ID {artist_id}.")

def main():
    parser = argparse.ArgumentParser(description="Spotify API Top Songs Scraper")
    parser.add_argument("-a", type=str, help="Name of the artist to get top songs for")
    args = parser.parse_args()

    lyrics_dir = "lyrics"
    os.makedirs(lyrics_dir, exist_ok=True)
    
    artist_name = args.a

    lyrics_dict = {}

    try:
        token = get_access_token()
        artist_id = get_artist_id(token, artist_name)
        top_songs = get_artist_top_songs(token, artist_id)

        if top_songs:
            for song in top_songs:
                song_name = song["name"]
                lyrics = get_lyrics(artist_name, song_name)
                lyrics_dict[song_name] = lyrics

        else:
            logger.error(f"No top songs found for artist {artist_name}.")
            raise Exception(f"No top songs found for artist {artist_name}.")

        with open(f"lyrics/{artist_name}_lyrics.json", "w") as f:
            json.dump(lyrics_dict, f, indent=4)
        logger.info(f"Lyrics for top songs of {artist_name} saved to {artist_name}_lyrics.json")

    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)

if __name__ == "__main__":
    main()

