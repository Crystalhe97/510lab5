import time
import requests
from bs4 import BeautifulSoup
import csv

# Function to scrape a single page
def scrape_page(url):
    try:
        res = requests.get(url)
        # Check if the request was successful
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            selector = "div.search-result-preview > div > h3 > a"
            a_eles = soup.select(selector)
            return [x['href'] for x in a_eles]
        else:
            print(f"Failed to retrieve page: {url}")
            return []
    except Exception as e:
        print(f"Error occurred: {e}")
        return []

# Main scraping function
def scrape_events(base_url, pages):
    all_urls = []
    for i in range(1, pages + 1):
        time.sleep(1)  # Delay to respect the server
        page_url = f"{base_url}/page/{i}"
        urls = scrape_page(page_url)
        all_urls.extend(urls)
        print(f"Scraped page {i}, found {len(urls)} URLs")
    return all_urls

# Base URL for the events list
base_url = "https://visitseattle.org/events"
pages = 48

# Scrape the events
event_urls = scrape_events(base_url, pages)
print(event_urls)

# Print the URLs in the requested format
print("[")
for url in event_urls:
    print(f" '{url}',")
print("]")