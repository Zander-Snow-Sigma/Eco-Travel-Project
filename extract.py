"""Script used in extracting data from APIs."""

import json
from os import environ

from dotenv import load_dotenv
import requests

load_dotenv()

COUNTRY_CODE = "GB"

POSTCODE_BASE_URL = "https://api.postcodes.io/postcodes"
TRAVEL_BASE_URL = "https://preview.api.climatiq.io/travel/v1-preview1/distance"


TEST_DATA = {
    "travel_mode": "car",
    "origin": {
        "latitude": 51.486881,
        "longitude": -2.768460,
        "country": "GB"
    },
    "destination": {
        "latitude": 51.434114,
        "longitude": -2.865147,
        "country": "GB"
    },
    "car_details": {
        "car_size": "medium",
        "car_type": "hybrid"
    }
}


ADDRESS_BASE_URL = "https://uk-postcode.p.rapidapi.com/getpostcode"

ADDRESS_HEADERS = {
    "X-RapidAPI-Key": environ['ADDRESS_API_KEY'],
    "X-RapidAPI-Host": environ['ADDRESS_API_HOST']
}


def get_raw_car_data(car_size: str, car_type: str) -> dict:
    """Returns the raw CO2e data from the """

    pass


def get_address(postcode: str) -> str:
    """Gets the address from the given postcode."""

    query = {"postcode": postcode}

    res = requests.get(ADDRESS_BASE_URL, headers=ADDRESS_HEADERS, params=query)

    if res.status_code == 200:

        data = res.json()['result']

        street_name = data.get('streetName')

        town = data.get('locality')

        return f"{street_name}, {town}"

    print(res.json())


def is_valid_postcode(postcode: str) -> bool:
    """Determines whether the given postcode is valid or not."""

    res = requests.get(f"{POSTCODE_BASE_URL}/{postcode}/validate", timeout=10)

    if res.status_code == 200:

        return res.json()['result']

    raise ConnectionError("Could not connect to the API.")


def get_raw_data(url: str, headers: dict) -> dict:
    """Returns the raw data from the Climatiq API."""

    res = requests.post(url, json=TEST_DATA, headers=headers, timeout=10)

    if res.status_code == 200:

        return res.json()
    raise ConnectionError("Could not connect to the API.")


def get_total_co2(data: dict) -> float:
    """Returns the total CO2e emissions."""

    return data['co2e']


if __name__ == "__main__":

    climatiq_headers = {'Authorization': f"Bearer: {environ['API_KEY']}"}

    raw_data = get_raw_data(TRAVEL_BASE_URL, headers=climatiq_headers)

    print(get_total_co2(raw_data))

    address = get_address("BS20 8BL")

    print(address)
