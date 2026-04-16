import pandas as pd
from ingestion.utils import engine
import numpy as np
def load_df(name: str) -> pd.DataFrame:
    df_forecast_features = pd.read_sql(f"SELECT * FROM {name}", engine)
    print(df_forecast_features.keys())
    return df_forecast_features

def time_mapping( time: int, period: int,name: str,):
    time_sin = np.sin(2*np.pi * time / period)
    time_cos = np.cos(2*np.pi * time / period)
    return pd.DataFrame({f"{name}_sin": time_sin, f"{name}_cos": time_cos})

def build_features(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    hour_map = time_mapping(df["hourly"].dt.hour, 24, 'hour')
    month_map = time_mapping(df["hourly"].dt.month, 12, 'months')
    day_of_year_map = time_mapping(df["hourly"].dt.day_of_year, 356, 'day_of_year')
    features = pd.concat([month_map, day_of_year_map, hour_map, df["avg_shortwave_radiation"],
                df["avg_wind_speed_10m"],df["avg_cloud_cover"], df["avg_temperature_2m"], df["avg_diffuse_radiation"]], axis=1)


    targets = pd.concat([df["solar_generation"], df["wind_generation_on"], df['wind_generation_off'],
                        (df["solar_generation"] + df["wind_generation_on"] + df['wind_generation_off']).rename("renewable_total_mw")], axis=1)
    print(targets)
    return features, targets
    
df = load_df('v_forecast_features')
build_features(df)