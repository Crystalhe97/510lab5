import re
import json
import datetime
from zoneinfo import ZoneInfo
import html
import requests
from db import get_db_conn



URL = 'https://visitseattle.org/events/page/'
URL_LIST_FILE = './data/links.json'
URL_DETAIL_FILE = './data/data.json'

def list_links():
    res = requests.get(URL + '1/')
    last_page_no = int(re.findall(r'bpn-last-page-link"><a href=".+?/page/(\d+?)/.+" title="Navigate to last page">', res.text)[0])

    links = []
    for page_no in range(1, last_page_no + 1):
        res = requests.get(URL + str(page_no) + '/')
        links.extend(re.findall(r'<h3 class="event-title"><a href="(https://visitseattle.org/events/.+?/)" title=".+?">.+?</a></h3>', res.text))

    json.dump(links, open(URL_LIST_FILE, 'w'))

def fetch_geolocation(location_name):
    """Fetch geolocation (latitude and longitude) for a given location name."""
    base_url = "https://nominatim.openstreetmap.org/search"
    params = {
        'q': location_name,
        'format': 'json',
        'limit': 1
    }
    headers = {
        'User-Agent': 'EventScraperBot 1.0'  # Change this to a more descriptive user-agent for your application
    }
    response = requests.get(base_url, params=params, headers=headers)
    if response.status_code == 200:
        data = response.json()
        if data:
            return {
                'latitude': data[0]['lat'],
                'longitude': data[0]['lon']
            }
    return None

def fetch_weather(latitude, longitude):
    """Fetch weather data for the given latitude and longitude from NWS."""
    gridpoint_url = f"https://api.weather.gov/points/{latitude},{longitude}"
    response = requests.get(gridpoint_url)
    if response.status_code == 200:
        gridpoint_data = response.json()
        forecast_url = gridpoint_data['properties']['forecast']

        forecast_response = requests.get(forecast_url)
        if forecast_response.status_code == 200:
            forecast_data = forecast_response.json()
            period = forecast_data['properties']['periods'][0]
            return {
                'weather_condition': period['shortForecast'],
                'temperature_max': period['temperature'],
                'temperature_min': None,  # Adjust logic if needed
                'wind_chill': None  # Adjust logic if needed
            }
    return None   
 

def get_detail_page():
    links = json.load(open(URL_LIST_FILE, 'r'))
    data = []
    for link in links:
        try:
            row = {}
            res = requests.get(link)
            row['title'] = html.unescape(re.findall(r'<h1 class="page-title" itemprop="headline">(.+?)</h1>', res.text)[0])
            datetime_venue = re.findall(r'<h4><span>.*?(\d{1,2}/\d{1,2}/\d{4})</span> \| <span>(.+?)</span></h4>', res.text)[0]
            row['date'] = datetime.datetime.strptime(datetime_venue[0], '%m/%d/%Y').replace(tzinfo=ZoneInfo('America/Los_Angeles')).isoformat()
            row['venue'] = datetime_venue[1].strip()
            metas = re.findall(r'<a href=".+?" class="button big medium black category">(.+?)</a>', res.text)
            row['category'] = html.unescape(metas[0])
            row['location'] = metas[1]

            # Fetch geolocation data
            geolocation = fetch_geolocation(row['location'])
            if geolocation:
                row['latitude'] = geolocation['latitude']
                row['longitude'] = geolocation['longitude']
            else:
                row['latitude'] = None
                row['longitude'] = None
        
            if geolocation:
                row['latitude'] = geolocation['latitude']
                row['longitude'] = geolocation['longitude']
        
                weather = fetch_weather(row['latitude'], row['longitude'])
                if weather:
                    row.update(weather)
                else:
                    row['weather'] = 'Not available'

            data.append(row)
        except IndexError as e:
            print(f'Error: {e}')
            print(f'Link: {link}')
    json.dump(data, open(URL_DETAIL_FILE, 'w'))

def insert_to_pg():
    q = '''
    CREATE TABLE IF NOT EXISTS events (
        url TEXT PRIMARY KEY,
        title TEXT,
        date TIMESTAMP WITH TIME ZONE,
        venue TEXT,
        category TEXT,
        location TEXT,
        latitude FLOAT,
        longitude FLOAT,
        weather_condition TEXT,
        temperature_max FLOAT,
        temperature_min FLOAT,
        wind_chill FLOAT
    );
    '''

    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute(q)
    
    urls = json.load(open(URL_LIST_FILE, 'r'))
    data = json.load(open(URL_DETAIL_FILE, 'r'))
    for url, row in zip(urls, data):
        q_insert = '''
        INSERT INTO events (url, title, date, venue, category, location, latitude, longitude, weather_condition, temperature_max, temperature_min, wind_chill)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (url) DO NOTHING;
        '''
        cur.execute(q_insert, (
            url, 
            row['title'], 
            row['date'], 
            row['venue'], 
            row['category'], 
            row['location'],
            row.get('latitude'),
            row.get('longitude'),
            row.get('weather_condition'),  
            row.get('temperature_max'),
            row.get('temperature_min'),
            row.get('wind_chill')
        ))
    conn.commit()
    cur.close()
    conn.close()
    

if __name__ == '__main__':
    list_links()
    get_detail_page()
    insert_to_pg()