# dvc_scrape_artists.py

import requests
from bs4 import BeautifulSoup
import logging

# Configure logging to display timestamps and log levels
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def scrape_billboard_100_artists():
    """
    Scrapes the Billboard Artist 100 chart page to extract artist names.

    Returns:
    --------
    list of str
        A deduplicated list of artist names currently featured in the Artist 100 chart.
    """
    url = 'https://www.billboard.com/charts/artist-100/'
    headers = {'User-Agent': 'Mozilla/5.0'}  # Helps avoid being blocked by the website

    try:
        # Send a GET request to the Billboard Artist 100 chart page
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Select artist name elements using CSS selectors based on Billboard's HTML structure
        artist_elements = soup.select('h3.c-title.a-no-trucate.a-font-primary-bold-s')

        # Extract text from each element and remove duplicates
        artists = [artist.get_text(strip=True) for artist in artist_elements]
        logging.info(f"Found {len(artists)} artists.")
        return list(set(artists))

    except Exception as e:
        logging.error(f"Error scraping Billboard: {e}")
        return []


if __name__ == "__main__":
    # Scrape the artist names and save them to a text file
    artists = scrape_billboard_100_artists()
    with open('scraped_artists.txt', 'w') as f:
        f.write('\n'.join(artists))
