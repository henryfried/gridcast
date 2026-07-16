import pandas as pd
import numpy as np

def time_mapping( time: int, period: int,name: str,):
    time_sin = np.sin(2*np.pi * time / period)
    time_cos = np.cos(2*np.pi * time / period)
    return pd.DataFrame({f"{name}_sin": time_sin, f"{name}_cos": time_cos})

def build_features(df: pd.DataFrame, capacity_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    hour_map = time_mapping(df["hourly"].dt.hour, 24, 'hour')
    month_map = time_mapping(df["hourly"].dt.month, 12, 'months')
    day_of_year_period = np.where(df["hourly"].dt.is_leap_year, 366, 365)
    day_of_year_map = time_mapping(df["hourly"].dt.day_of_year, day_of_year_period, 'day_of_year')

    year = df["hourly"].dt.year.rename("year")
    capacity_matched = pd.merge(
        year.to_frame(),
        capacity_df.assign(year=capacity_df["time_stamp"].dt.year),
        on="year",
        how="left",
        validate="many_to_one",
    )
    capacity_cols = ["solar_generation_capacity", "wind_generation_on_capacity", "wind_generation_off_capacity"]
    capacity_matched[capacity_cols] = capacity_matched[capacity_cols].replace(0, np.nan)

    features = pd.concat([month_map, day_of_year_map, hour_map, df["avg_shortwave_radiation"],
                df["avg_wind_speed_10m"], df["avg_cloud_cover"], df["avg_temperature_2m"],
                df["avg_diffuse_radiation"], df["avg_wind_speed_10m_off"]], axis=1)

    targets = pd.concat([(df["solar_generation"] / capacity_matched['solar_generation_capacity']).rename("solar_generation"),
                         (df["wind_generation_on"] / capacity_matched['wind_generation_on_capacity']).rename("wind_generation_on"),
                         (df['wind_generation_off'] / capacity_matched['wind_generation_off_capacity']).rename("wind_generation_off"),
                        ((df["solar_generation"] + df["wind_generation_on"] + df['wind_generation_off']) /
                        (capacity_matched['solar_generation_capacity'] + capacity_matched['wind_generation_on_capacity'] + capacity_matched['wind_generation_off_capacity'])).rename("renewable_total_capacity_factor")], axis=1)
    
    return features, targets

def build_sequences(X: np.ndarray, y: np.ndarray, window_size: int = 24) -> tuple[np.ndarray, np.ndarray]:
    n_samples = len(X) - window_size
    
    X_seq = []
    y_seq = []
    for n in range(n_samples):
        X_seq.append(X[n:n+window_size])
        y_seq.append(y[n+window_size])
  
    return np.array(X_seq), np.array(y_seq)
