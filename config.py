"""Config for the dashboard."""

from os import environ

from dotenv import load_dotenv
import pandas as pd

load_dotenv()

CLIMATIQ_HEADERS = {'Authorization': f"Bearer: {environ['API_KEY']}"}

STATIONS_DATA = pd.read_csv('./data/stations.csv')
AIRPORTS_DATA = pd.read_csv(
    './data/airports.csv').dropna(axis=0, subset=['iata_code'])
CAR_SIZE_DATA = pd.read_csv("./data/car_sizes.csv")
