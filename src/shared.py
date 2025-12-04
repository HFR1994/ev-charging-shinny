import ast
import json
import os
import random
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from pandas import DataFrame


def get_data_from_api(url: str = "https://charging.eviny.no/api/map/chargingStations") -> dict:
    """
    Fetches data from a GET API endpoint using the standard library.
    
    Args:
        url (str): The API endpoint URL.
        
    Returns:
        dict: The parsed JSON response from the API.
        
    Raises:
        urllib.error.URLError: If there is a network issue.
        json.JSONDecodeError: If the response is not valid JSON.
    """
    try:
        with urllib.request.urlopen(url) as response:
            if response.status == 200:
                data = response.read()
                return json.loads(data)
            else:
                print(f"Error: API returned status code {response.status}")
                return {}
    except urllib.error.URLError as e:
        print(f"Network error: {e}")
        return {}
    except json.JSONDecodeError as e:
        print(f"JSON decoding error: {e}")
        return {}

def parse_array(column: str):
    """
    Transforms str to an array

    Args:
        data_dir (str): CSV folder path.

    Returns:
        tuple: With two data frames.
    """
    try:
        return ast.literal_eval(column) if isinstance(column, str) else []
    except:
        return []


def load_data_into_pandas(data_dir: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Transforms processed CSV data into two separate dataframes

    - A table with charging station details (e.g. location, ID, name, status, etc.)
    - A table with utilization data (e.g. charging sessions or availability) timestamped.

    Args:
        data_dir (str): CSV folder path.

    Returns:
        tuple: With two data frames.
    """

    # Charging Data #
    charging_data = load_csv_data(os.path.join(data_dir, "charging_stations.csv"))

    # Utilization Data #
    utilization_data = load_csv_data(os.path.join(data_dir, "tariff_historical.csv"))

    # Fix amenities
    charging_data["amenities"] = charging_data["amenities"].apply(parse_array)

    return charging_data, utilization_data


def load_csv_data(file_name: str) -> pd.DataFrame:
    """
    Loads a processed data file from disk.

    Args:
        file_name (str): RAW JSON Data.

    Returns:
        DataFrame: A dataframe with charging station details.
    """

    return pd.read_csv(file_name)

def _random_unix_timestamp(last_timestamp: int, days: int =30) -> int:
    """
    Generates a random unix timestamp.

    Args:
        last_timestamp (str): Starting timestamp point.
        days (int): How many days to go back.

    Returns:
        int: The unix timestamp.
    """
    end = datetime.fromtimestamp(last_timestamp)
    start = end - timedelta(days=days)
    random_dt = start + (end - start) * random.random()
    return int(random_dt.timestamp())


def _random_price(currency):
    """Generate realistic price depending on currency."""
    if currency in ["DKK", "kr"]:
        return round(random.uniform(2.0, 7.0), 2)
    if currency == "EUR":
        return round(random.uniform(0.20, 0.90), 2)
    if currency == "SEK":
        return round(random.uniform(2.0, 12.0), 2)
    return round(random.uniform(1.0, 6.0), 2)


def inject_random_data(number: int, alternatives:list, utilization_data: pd.DataFrame) -> tuple[DataFrame, str]:
    """
    Generates random data using an existing dataframe as template.

    Args:
        number (int): Number of data points to generate.
        alternatives (list): Possible station alternatives .
        utilization_data (DataFrame): utilization dataframe.

    Returns:
        DataFrame: New concatenated dataframe.
        str: The station id randomly picked
    """
    rows = []

    chargers_by_station = {
        st: utilization_data[utilization_data["station_id"] == st]["id"].unique().tolist()
        for st in alternatives
    }

    station_id = random.choice(alternatives)

    for _ in range(number):
        charger_id = random.choice(chargers_by_station[station_id])

        template = utilization_data[
            (utilization_data["station_id"] == station_id) &
            (utilization_data["id"] == charger_id)
        ]

        connection_type = template["connection_type"].iloc[0]
        currency = template["currency"].iloc[0]
        timestamp = template["timestamp"].iloc[0]

        rows.append([
            station_id,
            connection_type,
            charger_id,
            _random_price(currency),
            "kWh",
            "",  # extra_tariff placeholder
            currency,
            False,  # has_vat
            "",  # vat_location
            _random_unix_timestamp(timestamp)
        ])

    simulated_df = pd.DataFrame(rows, columns=utilization_data.columns)

    return pd.concat([utilization_data, simulated_df], ignore_index=True), station_id

app_dir = Path(__file__).parent.parent
assets_dir = app_dir / "assets"