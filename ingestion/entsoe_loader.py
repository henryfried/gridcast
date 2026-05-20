"""Fetches generation and load data from the ENTSO-E Transparency Platform REST API."""

from __future__ import annotations

import pandas as pd
from entsoe import EntsoePandasClient
from dotenv import load_dotenv
import os

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env.postgres"))
api_key = os.environ.get("ENTSOE_API_KEY")

client = EntsoePandasClient(api_key=api_key)
COUNTRY_CODE = "DE_LU"
NEIGHBORS = ["FR",
             "NL",
             "BE",
             "AT",
             "CH",
             "CZ",
             "PL",
             "DK_1",
             "DK_2"]


def _fetch_load(
  country_code: str,
  start_date: str,
  end_date: str,
  time_zone: str = 'CET',
):
    """Fetch actual total load for a country zone.

    Returns a DataFrame with columns: country_code, time_stamp, total_load (MW).
    """
    df = client.query_load(country_code, start=pd.Timestamp(start_date, tz=time_zone), end=pd.Timestamp(end_date, tz=time_zone))
    df = df.reset_index()
    df.columns = ["time_stamp", "total_load"]
    df.insert(0, "country_code", country_code)
    return df

def _fetch_generation(
  country_code: str,
  start_date: str,
  end_date: str,
  time_zone: str = 'CET',
):
    """Fetch actual aggregated renewable generation for a country zone.

    Extracts Solar, Wind Offshore, and Wind Onshore from the full generation mix.
    Returns a DataFrame with columns: country_code, time_stamp, solar_generation, wind_generation_off, wind_generation_on (all MW).
    """
    df = client.query_generation(country_code, start=pd.Timestamp(start_date, tz=time_zone), end=pd.Timestamp(end_date, tz=time_zone))

    df = df.reset_index()
    timestamps = df['index']
    
    df_aggreg = df.xs('Actual Aggregated', axis=1, level=1)

    df_renewable = df_aggreg[['Solar', 'Wind Offshore', 'Wind Onshore']].copy()
    df_renewable = df_renewable.rename(columns={
        'Solar': 'solar_generation',
        'Wind Offshore': 'wind_generation_off',
        'Wind Onshore': 'wind_generation_on',
    })
    df_renewable.insert(0, "time_stamp", timestamps)
    df_renewable.insert(0, "country_code", country_code)

    return df_renewable

def _fetch_capacities(
    country_code: str,
    start_date: str,
    end_date: str,
    time_zone: str = 'CET',
):
    df = client.query_installed_generation_capacity(country_code, start=pd.Timestamp(start_date, tz=time_zone), end=pd.Timestamp(end_date, tz=time_zone))
    df = df.reset_index()
    timestamps = df['index']

    df_renewable_capacities = df[['Solar', 'Wind Offshore', 'Wind Onshore']].copy()
    df_renewable_capacities = df_renewable_capacities.rename(columns={
        'Solar': 'solar_generation_capacity',
        'Wind Offshore': 'wind_generation_off_capacity',
        'Wind Onshore': 'wind_generation_on_capacity',
    })
    df_renewable_capacities.insert(0, "time_stamp", timestamps)
    df_renewable_capacities.insert(0, "country_code", country_code)

    return df_renewable_capacities
    
def _fetch_flows(
  country_code: str,
  start_date: str,
  end_date: str,
  neighbors: str,
  time_zone: str = 'CET',
):
    """Fetch cross-border physical flows from a country zone to each of its neighbors.

    Iterates over `neighbors`, querying one bilateral flow per pair.
    Returns a single long-format DataFrame with columns: time_stamp, from_zone, to_zone, flow_mw.
    Rows are sorted by time_stamp.
    """
    frames = []
    for country_to in neighbors:
        df = client.query_crossborder_flows(country_code_from=country_code,
                                        country_code_to=country_to,
                                        start=pd.Timestamp(start_date, tz=time_zone),
                                        end=pd.Timestamp(end_date, tz=time_zone))
        df = df.reset_index()
        df.columns = ["time_stamp", "flow_mw"]
        df.insert(1, "to_zone", country_to)
        frames.append(df)
    
    df_flow = pd.concat(frames,axis=0)
    df_flow.insert(1, "from_zone", country_code)
    df_flow = df_flow.sort_values("time_stamp").reset_index(drop=True)

    return df_flow


def load_entso_e(
    start_date: str,
    end_date: str,
    country_code: str | None = None,
    neighbors: list[str] | None = None,
) -> dict[str, pd.DataFrame]:
    """Fetch load, renewable generation, and cross-border flows from ENTSO-E.

    Args:
        start_date: ISO date string, e.g. "2023-01-01".
        end_date:   ISO date string, e.g. "2023-01-07".
        country_code: ENTSO-E zone code. Defaults to COUNTRY_CODE ("DE_LU").
        neighbors:  List of neighboring zone codes for flow queries. Defaults to NEIGHBORS.

    Returns:
        A dict with three DataFrames keyed by target table name:
            - "entso_e_load"
            - "entso_e_generation"
            - "entso_e_flows"
    """
    if country_code is None:
        country_code = COUNTRY_CODE
    if neighbors is None:
        neighbors = NEIGHBORS
    

    df_load = _fetch_load(country_code,
                    start_date,
                    end_date)
    
    df_generation = _fetch_generation(country_code,
                            start_date,
                            end_date)
    
    df_capacities = _fetch_capacities(country_code,
                            start_date,
                            end_date)

    df_flows = _fetch_flows(country_code,
                            start_date,
                            end_date,
                            neighbors)
    frames = {
            "entso_e_load": df_load,
            "entso_e_generation": df_generation,
            "entso_e_capacity": df_capacities,
            "entso_e_flows": df_flows
            }
           
    return frames
