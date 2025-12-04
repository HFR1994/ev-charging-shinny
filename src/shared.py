import ast
import json
import os
import urllib.request
import urllib.error
from pathlib import Path

import numpy as np
import pandas as pd

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

app_dir = Path(__file__).parent.parent
assets_dir = app_dir / "assets"