# dvc_scrape_artists.py
import requests
from bs4 import BeautifulSoup
import logging


def scrape_billboard_100_artists():
    url = 'https://www.billboard.com/charts/artist-100/'
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        artist_elements = soup.select('h3.c-title.a-no-trucate.a-font-primary-bold-s')
        artists = [artist.get_text(strip=True) for artist in artist_elements]
        logging.info(f"Found {len(artists)} artists.")
        return list(set(artists))
    except Exception as e:
        logging.error(f"Error scraping Billboard: {e}")
        return []


if __name__ == "__main__":
    artists = scrape_billboard_100_artists()
    with open('scraped_artists.txt', 'w') as f:
        f.write('\n'.join(artists))
