import json
import urllib.request
import urllib.error

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


def convert_data_into_pandas(raw_data: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Transforms RAW JSON data into two seperate dataframes

    - A table with charging station details (e.g. location, ID, name, status, etc.)
    - A table with utilization data (e.g. charging sessions or availability) timestamped by hour.

    Args:
        raw_data (dict): RAW JSON Data.

    Returns:
        tuple: With two data frames.
    """

    raw_df  = pd.json_normalize(raw_data["chargingStations"])

    # Charging Data #
    charging_data = gen_charging_data_df(raw_df)

    # Utilization Data #
    utilization_data = gen_utilization_data_df(raw_df)

    return charging_data, utilization_data


def gen_charging_data_df(raw_df: pd.DataFrame) -> pd.DataFrame:
    """
    Transforms RAW JSON data charging station details into a dataframe.

    Args:
        raw_df (dict): RAW JSON Data.

    Returns:
        DataFrame: A dataframe with charging station details.
    """

    charging_data = raw_df[
        ['id', 'name', 'address', 'description', 'location.lat', 'location.lng', 'amenities', 'totalConnectors']].copy()
    charging_data.rename({"location.lat": "latitud", "location.lng": "longitud"})
    return charging_data


def gen_utilization_data_df(raw_df: pd.DataFrame) -> pd.DataFrame:
    """
    Transforms RAW JSON data utilization data details into a dataframe.

    Args:
        raw_df (dict): RAW JSON Data.

    Returns:
        DataFrame: A dataframe with utilization data details.
    """
    conn_cols = [c for c in raw_df.columns if c.startswith("connectionsTypes.")]
    raw_col = []

    for _, row in raw_df.iterrows():
        station_id = row["id"]

        for col in conn_cols:
            conn_type = col.split(".", 1)[1]  # extract column type

            connectors = row[col] or []  # each is a list of dicts

            for item in connectors:
                raw_col.append({
                    "station_id": station_id,
                    "connection_type": conn_type,
                    **item
                })

    utilization_data = pd.DataFrame(raw_col)

    ## Random timestamp generation
    start = pd.Timestamp.now() - pd.Timedelta(hours=7)  # At most a car shouldn't plug in more than 7 hours ago
    end = pd.Timestamp.now()

    # total seconds in the range
    total_seconds = int((end - start).total_seconds())

    # generate random timestamps
    utilization_data["timestamp"] = start + pd.to_timedelta(
        np.random.randint(0, total_seconds, size=len(utilization_data)),
        unit="s"
    )
    return utilization_data