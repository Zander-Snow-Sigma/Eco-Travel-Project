"""Script used in extracting data from APIs."""

import json
from os import environ

from dotenv import load_dotenv
import pandas as pd
import requests

from config import CLIMATIQ_HEADERS

COUNTRY_CODE = "GB"

POSTCODE_BASE_URL = "https://api.postcodes.io/postcodes"
CLIMATIQ_URL = "https://preview.api.climatiq.io/travel/v1-preview1/distance"


ADDRESS_BASE_URL = "https://uk-postcode.p.rapidapi.com/getpostcode"


def get_postcode_location(postcode: str) -> str:
    """Gets the address from the given postcode."""

    res = requests.get(f"{POSTCODE_BASE_URL}/{postcode}")

    if res.status_code == 200:

        data = res.json()['result']

        parish = data.get('parish')

        if parish:

            name = parish.split(",")[0] if "," in parish else parish
        else:
            name = data.get('admin_ward')

        lat = data.get('latitude')
        long = data.get('longitude')

        return {'name': name, 'lat': lat, 'long': long}

    raise ConnectionError("Could not connect to the API.")


def is_valid_postcode(postcode: str) -> bool:
    """Determines whether the given postcode is valid or not."""

    res = requests.get(f"{POSTCODE_BASE_URL}/{postcode}/validate", timeout=10)

    if res.status_code == 200:

        return res.json()['result']

    raise ConnectionError("Could not connect to the API.")


def get_carbon_rail_data(origin_location: str, dest_location: str) -> dict:
    """Returns raw data about a rail journey from the Climatiq API."""

    co2e_data = dict()

    rail_data = {
        "travel_mode": "rail",
        "origin": {
            "latitude": origin_location['lat'],
            "longitude": origin_location['long'],
            "country": "GB"
        },
        "destination": {
            "latitude": dest_location['lat'],
            "longitude": dest_location['long'],
            "country": "GB"
        }
    }

    res = requests.post(CLIMATIQ_URL, json=rail_data,
                        headers=CLIMATIQ_HEADERS, timeout=10)

    if res.status_code == 200:

        data = res.json()

        co2e_data['co2e'] = data['co2e']
        co2e_data['direct_co2e'] = data['direct_emissions']['co2e']
        co2e_data['indirect_co2e'] = data['indirect_emissions']['co2e']
        co2e_data['distance'] = data['distance_km']

        return co2e_data

    raise ConnectionError("Could not connect to the API.")


def get_rail_location(station: str, stations_df: pd.DataFrame) -> dict:
    """Returns the latitude and longitude of the given railway station."""

    station_data = stations_df[stations_df['stationName'] == station]

    lat = station_data['lat'].values[0]
    long = station_data['long'].values[0]

    return {'lat': lat, 'long': long}


def get_rail_db_data(origin_station: str, dest_station: str, stations_df: pd.DataFrame) -> dict:
    """Returns a dictionary of all the necessary data from a rail journey to be inserted into the database."""

    journey_data = dict()

    journey_data['transport'] = dict()

    journey_data['transport']['type'] = 'rail'

    journey_data['origin'] = dict()

    origin_location = get_rail_location(origin_station, stations_df)

    journey_data['origin']['name'] = origin_station
    journey_data['origin']['lat'] = origin_location['lat']
    journey_data['origin']['lon'] = origin_location['long']

    journey_data['destination'] = dict()

    dest_location = get_rail_location(dest_station, stations_df)

    journey_data['destination']['name'] = dest_station
    journey_data['destination']['lat'] = dest_location['lat']
    journey_data['destination']['lon'] = dest_location['long']

    journey_data['co2e'] = dict()

    carbon_data = get_carbon_rail_data(origin_location, dest_location)

    journey_data['co2e']['total'] = carbon_data['co2e']
    journey_data['co2e']['direct'] = carbon_data['direct_co2e']
    journey_data['co2e']['indirect'] = carbon_data['indirect_co2e']

    journey_data['distance'] = carbon_data['distance']

    return journey_data


def get_car_carbon_data(origin_location: dict, dest_location: dict, car_details: dict) -> dict:
    """Returns the CO2e data of a given car journey from the Climatiq API."""

    co2e_data = dict()

    car_data = {
        "travel_mode": "car",
        "origin": {
            "latitude": origin_location['lat'],
            "longitude": origin_location['long'],
            "country": "GB"
        },
        "destination": {
            "latitude": dest_location['lat'],
            "longitude": dest_location['long'],
            "country": "GB"
        },
        "car_details": {
            "car_size": car_details['car_size'],
            "car_type": car_details['car_type']
        }
    }

    res = requests.post(CLIMATIQ_URL, json=car_data,
                        headers=CLIMATIQ_HEADERS, timeout=10)

    if res.status_code == 200:

        data = res.json()

        co2e_data['co2e'] = data['co2e']
        co2e_data['direct_co2e'] = data['direct_emissions']['co2e']
        co2e_data['indirect_co2e'] = data['indirect_emissions']['co2e']
        co2e_data['distance'] = data['distance_km']

        return co2e_data

    raise ConnectionError("Could not connect to the API.")


def get_car_db_data(origin_postcode: str, dest_postcode: str, car_details: dict) -> dict:
    """Returns a dictionary of all the necessary data from a rail journey to be inserted into the database."""

    journey_data = dict()

    journey_data['transport'] = dict()

    journey_data['transport']['type'] = 'car'
    journey_data['transport']['car_size'] = car_details['car_size']
    journey_data['transport']['car_type'] = car_details['car_type']

    journey_data['origin'] = dict()

    origin_location = get_postcode_location(origin_postcode)

    journey_data['origin']['name'] = origin_location['name']
    journey_data['origin']['lat'] = origin_location['lat']
    journey_data['origin']['lon'] = origin_location['long']

    journey_data['destination'] = dict()

    dest_location = get_postcode_location(dest_postcode)

    journey_data['destination']['name'] = dest_location['name']
    journey_data['destination']['lat'] = dest_location['lat']
    journey_data['destination']['lon'] = dest_location['long']

    journey_data['co2e'] = dict()

    carbon_data = get_car_carbon_data(
        origin_location, dest_location, car_details)

    journey_data['co2e']['total'] = carbon_data['co2e']
    journey_data['co2e']['direct'] = carbon_data['direct_co2e']
    journey_data['co2e']['indirect'] = carbon_data['indirect_co2e']

    journey_data['distance'] = carbon_data['distance']

    return journey_data


def get_airport_location(airport: str, airports_df: pd.DataFrame) -> dict:
    """Returns the location of a given airport."""

    airport_data = airports_df[airports_df['name'] == airport]

    lat = airport_data['latitude_deg'].values[0]
    long = airport_data['longitude_deg'].values[0]
    iata = airport_data['iata_code'].values[0]

    return {'lat': lat, 'long': long, 'iata': iata}


def get_flight_carbon_data(origin_location: dict, dest_location: dict, cabin_class: str) -> dict:
    """Returns CO2e data from a given flight."""

    co2e_data = dict()

    flight_data = {
        "travel_mode": "air",
        "origin": {
            "iata": origin_location['iata']
        },
        "destination": {
            "iata": dest_location['iata']
        },
        "air_details": {
            "class": cabin_class
        }
    }

    res = requests.post(CLIMATIQ_URL, json=flight_data,
                        headers=CLIMATIQ_HEADERS, timeout=10)

    if res.status_code == 200:

        data = res.json()

        co2e_data['co2e'] = data['co2e']
        co2e_data['direct_co2e'] = data['direct_emissions']['co2e']
        co2e_data['indirect_co2e'] = data['indirect_emissions']['co2e']
        co2e_data['distance'] = data['distance_km']

        return co2e_data

    raise ConnectionError("Could not connect to the API.")


def get_flight_db_data(origin_airport: str, dest_airport: str, cabin_class: str, airports_df: pd.DataFrame) -> dict:
    """Returns all the necessary data from a flight to insert into the database."""

    journey_data = dict()

    journey_data['transport'] = dict()

    journey_data['transport']['type'] = 'air'
    journey_data['transport']['cabin_class'] = cabin_class

    journey_data['origin'] = dict()

    origin_location = get_airport_location(origin_airport, airports_df)

    journey_data['origin']['name'] = origin_airport
    journey_data['origin']['lat'] = origin_location['lat']
    journey_data['origin']['lon'] = origin_location['long']

    journey_data['destination'] = dict()

    dest_location = get_airport_location(dest_airport, airports_df)

    journey_data['destination']['name'] = dest_airport
    journey_data['destination']['lat'] = dest_location['lat']
    journey_data['destination']['lon'] = dest_location['long']

    journey_data['co2e'] = dict()

    carbon_data = get_flight_carbon_data(
        origin_location, dest_location, cabin_class)

    journey_data['co2e']['total'] = carbon_data['co2e']
    journey_data['co2e']['direct'] = carbon_data['direct_co2e']
    journey_data['co2e']['indirect'] = carbon_data['indirect_co2e']

    journey_data['distance'] = carbon_data['distance']

    return journey_data


if __name__ == "__main__":

    load_dotenv()

    ADDRESS_HEADERS = {
        "X-RapidAPI-Key": environ['ADDRESS_API_KEY'],
        "X-RapidAPI-Host": environ['ADDRESS_API_HOST']
    }

    CLIMATIQ_HEADERS = {'Authorization': f"Bearer: {environ['API_KEY']}"}

    stations_df = pd.read_csv("./data/stations.csv")

    origin = "Bristol Temple Meads"
    dest = "Filton Abbey Wood"

    origin = "BS20 8BL"
    dest = "BS21 7TS"

    car_details = {'car_size': 'small', 'car_type': 'petrol'}

    car_journey = get_car_db_data(
        origin, dest, car_details, CLIMATIQ_HEADERS, ADDRESS_HEADERS)
