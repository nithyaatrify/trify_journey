import pandas as pd
import requests
from haversine import haversine, Unit
from tqdm import tqdm
import time
import logging

API_KEYS = [
    '5b3ce3597851110001cf6248617202d35c7742caaab67aa8be17e6c2',
    '5b3ce3597851110001cf6248a5b52add7f72445cbff5c145c12f79ba',
]

API_ENDPOINT = 'https://api.openrouteservice.org/v2/directions/driving-car'
WAIT_TIME_403 = 28 * 60 * 60  # 28 hours in seconds

logging.basicConfig(level=logging.INFO)

coordinates_df = pd.read_csv('coordinates.csv')

def calculate_distance(coord1, coord2):
    return haversine(coord1, coord2, unit=Unit.METERS)

def fetch_route_with_rate_limit(start_coord, end_coord):
    for api_key in API_KEYS:
        endpoint = f'{API_ENDPOINT}?api_key={api_key}&start={start_coord[1]},{start_coord[0]}&end={end_coord[1]},{end_coord[0]}'
        response = requests.get(endpoint)

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:
            logging.info(f"Rate limit exceeded for API key {api_key}. Waiting for 60 seconds...")
            time.sleep(60)
        elif response.status_code == 403:
            logging.info(f"Daily quota exceeded for API key {api_key}. Waiting for {WAIT_TIME_403} seconds...")
            time.sleep(WAIT_TIME_403)
        else:
            logging.error(f"Failed to fetch route: {response.status_code}")
            return None

    logging.error("All available API keys have exceeded the daily limit.")
    return "403_error"

journeys = []
total_journeys = (len(coordinates_df) * (len(coordinates_df) - 1)) // 2
continue_generation = True

with tqdm(total=total_journeys, desc="Fetching routes") as pbar:
    for i in range(len(coordinates_df)):
        for j in range(i + 1, len(coordinates_df)):
            if not continue_generation:
                while True:
                    user_input = input("Enter 'continue generation' to resume: ")
                    if user_input.lower() == 'continue generation':
                        continue_generation = True
                        break

            if not continue_generation:
                break

            start_coord = (coordinates_df.loc[i, 'Latitude'], coordinates_df.loc[i, 'Longitude'])
            end_coord = (coordinates_df.loc[j, 'Latitude'], coordinates_df.loc[j, 'Longitude'])
            distance = calculate_distance(start_coord, end_coord)

            route_details = fetch_route_with_rate_limit(start_coord, end_coord)
            if route_details:
                waypoints = route_details['features'][0]['geometry']['coordinates']
                journey = {'Journey Id': f"{i + 1}:{j + 1}"}
                journey['JS0'] = f"{start_coord[0]}, {start_coord[1]}"
                journey['JSN'] = f"{end_coord[0]}, {end_coord[1]}"
                for step, waypoint in enumerate(waypoints):
                    journey[f'JS{step + 1}'] = f"{waypoint[1]}, {waypoint[0]}"
                journeys.append(journey)

            pbar.update(1)
            pbar.set_postfix({"Completed Journeys": len(journeys)})

output_df = pd.DataFrame(journeys)
output_df.to_csv('waypoints.csv', index=False)
