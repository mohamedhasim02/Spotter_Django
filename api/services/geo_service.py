from django.conf import settings
from opencage.geocoder import OpenCageGeocode
import json
import openrouteservice
from shapely.geometry import LineString, Point
from geopy.distance import geodesic
import os
from .geo_service import *
from .folium_service import *
import pandas as pd
from functools import reduce
import geopandas as gpd
from shapely.geometry import Point

#> Geocode
def get_lat_lon(address, api_key):
    # Initialize the geocoder
    geocoder = OpenCageGeocode(api_key)
    
    # Geocode the address
    result = geocoder.geocode(address)
    
    if result:
        # Extract latitude and longitude from the result
        lat = result[0]['geometry']['lat']
        lon = result[0]['geometry']['lng']
        return lat, lon
    else:
        return None, None

#> Open Route 
def call_openroute_service_by_car(start_coords:list[int]  , end_coords:list[int]):
    '''
        coords in this format : [lat , long]
    '''
    openroute_key = os.getenv("OPENROUTE_SERVICE_KEY")
    client = openrouteservice.Client(key=openroute_key)

    start_coords = (start_coords[1], start_coords[0])
    end_coords = (end_coords[1], end_coords[0])

    route = client.directions( coordinates=[start_coords, end_coords], profile='driving-car', format='geojson'
    )
    return route

#> Finds coordinates after x miles
def find_position_on_route(route_coords, target_distance_miles):
    
    cumulative_distance = 0

    for i in range(len(route_coords) - 1):
        start = route_coords[i]
        end = route_coords[i + 1]

        # Calculate distance between consecutive points
        segment_distance = geodesic(start, end).miles

        if cumulative_distance + segment_distance >= target_distance_miles:
            # Interpolate the position
            remaining_distance = target_distance_miles - cumulative_distance
            fraction = remaining_distance / segment_distance

            # Interpolate latitude and longitude
            lat = start[0] + fraction * (end[0] - start[0])
            lon = start[1] + fraction * (end[1] - start[1])

            return lat, lon

        cumulative_distance += segment_distance

    return route_coords[-1]


#> Helper (not used)
def calculate_route_total_distance(route_coords):
    total_distance = 0

    for i in range(len(route_coords) - 1):
        start = route_coords[i]
        end = route_coords[i + 1]
        segment_distance = geodesic(start, end).miles
        total_distance += segment_distance
    return total_distance

#> Gets stops coordinates even x miles (max car distance here) 
def calculate_stops_on_route(route_coords, interval_miles , total_distance):
    """
    Calculate stops at each interval along the route.

    :param route_coords: List of coordinates (latitude, longitude) representing the route.
    :param interval_miles: Distance interval (in miles) for stops.
    :return: List of coordinates (latitude, longitude) for each stop.
    """
    stops = []
    # total_distance = calculate_route_total_distance(route_coords)

    target_distance = interval_miles
    while target_distance <= total_distance:
        stop = find_position_on_route(route_coords, target_distance)
        stops.append(stop)
        target_distance += interval_miles

    return stops

#> Gets cheapest gas station around a radius (used 200)
def find_cheapest_gas_station(stops, gas_stations, radius_miles=5):
    """
    Finds the cheapest gas station near each stop within the given radius.

    :param stops: List of coordinates (latitude, longitude) for the stops.
    :param gas_stations: DataFrame with gas station information, including 'Latitude', 'Longitude', and 'Retail Price'.
    :param radius_miles: Radius (in miles) to search for nearby gas stations.
    :return: List of dictionaries with stop coordinates and the cheapest gas station details.
    """
    results = []

    for stop in stops:
        stop_lat, stop_lon = stop
        stop_point = (stop_lat, stop_lon)

        # Calculate distances to all gas stations
        gas_stations['Distance'] = gas_stations.apply(
            lambda row: geodesic(stop_point, (row['Latitude'], row['Longitude'])).miles,
            axis=1
        )
        sorted_gas_stations = gas_stations.sort_values(by='Distance', ascending=True)

        # Filter gas stations within the radius
        nearby_stations = gas_stations[gas_stations['Distance'] <= radius_miles]

        if not nearby_stations.empty:
            # Find the cheapest gas station
            cheapest_station = nearby_stations.loc[nearby_stations['Retail Price'].idxmin()]
            results.append({
                'Stop': stop,
                'Station': {
                    'Name': cheapest_station['Truckstop Name'],
                    'Address': cheapest_station['Address'],
                    'City': cheapest_station['City'],
                    'State': cheapest_station['State'],
                    'Latitude': cheapest_station['Latitude'],
                    'Longitude': cheapest_station['Longitude'],
                    'Price': cheapest_station['Retail Price'],
                    'Distance': cheapest_station['Distance']
                }
            })
        else:
            # No gas station found within the radius
            results.append({
                'Stop': stop,
                'Station': None
            })
    

    return results

#> helper
def meters_to_miles(meters):
    return meters * 0.000621371

#> view logic for cleanup
def resolve_route_fuel_request(validated_data):
    # {latitude : 1 , longitude: -1}
        start = validated_data.get("start_coordinates")
        start_coords = (start["latitude"], start["longitude"])

        end = validated_data.get("end_coordinates")
        end_coords = (end["latitude"], end["longitude"])

        car_mpg = validated_data.get("car_mpg")
        car_max_miles = validated_data.get("car_max_miles")


        route = call_openroute_service_by_car(start_coords, end_coords)
        route_geometry = route["features"][0]["geometry"]
        
        waypoints = [(lat, lon) for lon, lat in route_geometry["coordinates"]] 
        total_distance = meters_to_miles(route["features"][0]["properties"]["summary"]["distance"])

        map = create_route_map(route , start_coords, end_coords)

        gas_station_stops = calculate_stops_on_route(waypoints , car_max_miles, total_distance)

        csv_file_path = os.path.join(settings.BASE_DIR, 'api', 'data', 'cleaned_fuel_prices_file.csv')
        gas_stations =  pd.read_csv(csv_file_path)

        station_stops = find_cheapest_gas_station(gas_station_stops , gas_stations , 200)

        for item in station_stops:
            stop,station = item["Stop"] , item["Station"]
            folium.Marker((stop[0], stop[1]), popup="stop", icon=folium.Icon(color="blue")).add_to(map)

            folium.Marker((station["Latitude"], station["Longitude"]), popup="Station", icon=folium.Icon(color="purple")).add_to(map)
            folium.Marker(
                (station["Latitude"]-0.0001, station["Longitude"]),
                popup="station",
                icon=folium.DivIcon(html=f'''
                    <div style="font-size: 12px; text-align: center;">
                        <div style="color: white; font-weight: bold; margin-bottom: 5px;">{station["Name"]}</div>
                        <div style="color: #90ee90; font-weight: bold;">${station["Price"]}</div>
                    </div>
                ''')
                ).add_to(map)


        car_gpm = car_max_miles//car_mpg
        total_fuel_price = reduce(
            lambda acc, entry: acc + entry['Station']['Price'] * car_gpm,
            station_stops,
            0
            )
        
        return total_fuel_price, map

#> validates if coords are within US (not included in hosted)
def is_within_us(lat, lon):
    # Load the GeoJSON file for US boundaries
    usa_geo_json_path = os.path.join(settings.BASE_DIR, 'api', 'data', 'USA.geo.json')
    us_boundary = gpd.read_file(usa_geo_json_path)
    
    # Create a Point object for the given coordinates
    point = Point(lon, lat)
    
    # Check if the point is within the US boundary
    return us_boundary.contains(point).any()