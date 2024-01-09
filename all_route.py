import pandas as pd
import requests
from haversine import haversine, Unit
from tqdm import tqdm
import time

# Load coordinates from the CSV file
coordinates_df = pd.read_csv('coordinates.csv')

# Function to calculate distance between two coordinates using Haversine formula
def calculate_distance(coord1, coord2):
    return haversine(coord1, coord2, unit=Unit.METERS)

# Function to fetch route details from OpenRouteService API with rate limiting
def fetch_route_with_rate_limit(start_coord, end_coord, api_key):
    endpoint = f'https://api.openrouteservice.org/v2/directions/driving-car?api_key={api_key}&start={start_coord[1]},{start_coord[0]}&end={end_coord[1]},{end_coord[0]}'
    response = requests.get(endpoint)
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 429:
        print(f"Rate limit exceeded. Waiting for retry...")
        time.sleep(60)  # Wait for 60 seconds to respect per minute limit
        return fetch_route_with_rate_limit(start_coord, end_coord, api_key)  # Retry the request
    else:
        print(f"Failed to fetch route: {response.status_code}")
        return None

# Generate all possible journeys and waypoints
journeys = []
journey_id = 1
api_key = '5b3ce3597851110001cf62487ebcbc97ae02431496a28074fb7c1f44'  # Replace with your actual API key
total_journeys = (len(coordinates_df) * (len(coordinates_df) - 1)) // 2  # Total number of journeys

with tqdm(total=total_journeys, desc="Fetching routes") as pbar:
    for i in range(len(coordinates_df)):
        for j in range(i + 1, len(coordinates_df)):
            start_coord = (coordinates_df.loc[i, 'Latitude'], coordinates_df.loc[i, 'Longitude'])
            end_coord = (coordinates_df.loc[j, 'Latitude'], coordinates_df.loc[j, 'Longitude'])
            distance = calculate_distance(start_coord, end_coord)
            
            # Fetch route details with rate limiting
            route_details = fetch_route_with_rate_limit(start_coord, end_coord, api_key)
            if route_details:
                waypoints = route_details['features'][0]['geometry']['coordinates']
                journey = {'Journey Id': journey_id}
                for step, waypoint in enumerate(waypoints):
                    journey[f'JS{step + 1}'] = f"{waypoint[1]}, {waypoint[0]}"
                journeys.append(journey)
                journey_id += 1
                
            pbar.update(1)  # Update progress bar
            pbar.set_postfix({"Completed Journeys": journey_id - 1})  # Update completed journeys count in the progress bar

# Create a DataFrame and save as CSV
output_df = pd.DataFrame(journeys)
output_df.to_csv('waypoints_journeys.csv', index=False)
