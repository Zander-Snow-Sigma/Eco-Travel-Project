"""Unit tests for the extract script."""

import pandas as pd

from extract import get_airport_location


def test_get_airport_location():
    """Tests that the correct airport location is returned."""

    airports_df = pd.read_csv("./data/airports.csv")

    location = get_airport_location("Aksu Hongqipo Airport", airports_df)

    assert location == {'lat': 41.262501, 'long': 80.291702, 'iata': "AKU"}
