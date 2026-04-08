"""Fetches historical weather data from the Open-Meteo archive API."""

from __future__ import annotations

import requests
import pandas as pd

ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"

# Representative locations for the DE-LU bidding zone
LOCATIONS: dict[str, dict[str, float]] = {
    "berlin":     {"latitude": 52.52, "longitude": 13.40},
    "munich":     {"latitude": 48.14, "longitude": 11.58},
    "frankfurt":  {"latitude": 50.11, "longitude":  8.68},
    "hamburg":    {"latitude": 53.55, "longitude":  9.99},
    "cologne":    {"latitude": 50.94, "longitude":  6.96},
    "luxembourg": {"latitude": 49.61, "longitude":  6.13},
}

# Default hourly variables — chosen for net load and solar generation modelling
VARIABLES: list[str] = [
    "temperature_2m",
    "shortwave_radiation",
    "direct_radiation",
    "diffuse_radiation",
    "wind_speed_10m",
    "cloud_cover",
]


def _fetch_location(
    name: str,
    latitude: float,
    longitude: float,
    start_date: str,
    end_date: str,
    variables: list[str],
) -> pd.DataFrame:
    """Fetch hourly data for a single location and return a tidy DataFrame."""
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": ",".join(variables),
        "timezone": "Europe/Berlin",
    }
    response = requests.get(ARCHIVE_URL, params=params, timeout=30)
    response.raise_for_status()

    hourly = response.json()["hourly"]
    df = pd.DataFrame(hourly)
    df["time"] = pd.to_datetime(df["time"])
    df.rename(columns={"time": "time_stamp"}, inplace=True)
    df.insert(0, "loc", name)
    return df


def load_weather(
    start_date: str,
    end_date: str,
    locations: dict[str, dict[str, float]] | None = None,
    variables: list[str] | None = None,
) -> pd.DataFrame:
    """
    Load historical hourly weather data for DE-LU representative locations.

    Parameters
    ----------
    start_date : str
        ISO date string, e.g. "2022-01-01". Pass a year boundary to limit
        the fetch to a single year or a specific range.
    end_date : str
        ISO date string, e.g. "2022-12-31".
    locations : dict, optional
        Mapping of {name: {"latitude": float, "longitude": float}}.
        Defaults to the six DE-LU representative cities in LOCATIONS.
    variables : list[str], optional
        Open-Meteo hourly variable names. Defaults to VARIABLES.

    Returns
    -------
    pd.DataFrame
        Hourly weather data with columns:
        location, timestamp, <variable columns>

    Examples
    --------
    # Single year
    df = load_weather("2023-01-01", "2023-12-31")

    # Multi-year range
    df = load_weather("2020-01-01", "2023-12-31")

    # Custom locations
    df = load_weather("2023-01-01", "2023-12-31", locations={"berlin": {"latitude": 52.52, "longitude": 13.40}})
    """
    if locations is None:
        locations = LOCATIONS
    if variables is None:
        variables = VARIABLES

    frames: list[pd.DataFrame] = []
    for name, coords in locations.items():
        df = _fetch_location(
            name=name,
            latitude=coords["latitude"],
            longitude=coords["longitude"],
            start_date=start_date,
            end_date=end_date,
            variables=variables,
        )
        frames.append(df)

    return pd.concat(frames, ignore_index=True)
