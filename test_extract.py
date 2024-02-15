"""Unit tests for the extract script."""

from extract import get_total_co2


def test_get_total_co2():
    """Tests that the total CO2e is returned from the raw data."""

    test_data = {'co2e': 2.98}

    assert get_total_co2(test_data) == 2.98
