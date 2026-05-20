import numpy as np
import pandas as pd
import pytest

from models.features import time_mapping, build_features, build_sequences

def test_time_mapping():
    time = np.array([0, 6, 12, 18, 24, 30, 36])
    result = time_mapping(time, period=24, name='test')
    
    assert (result["test_sin"].between(-1, 1)).all()
    assert (result["test_cos"].between(-1, 1)).all()
    
    assert (result["test_sin"][0] == pytest.approx(0, abs=1e-6))
    assert (result["test_sin"][1] == pytest.approx(1, abs=1e-6))
    
    assert (result["test_cos"][0] == pytest.approx(1, abs=1e-6))
    assert (result["test_cos"][1] == pytest.approx(0, abs=1e-6))

@pytest.fixture
def dummy_df():
    return pd.DataFrame({
        'hourly': pd.date_range('2023-01-01', periods=24, freq='h', tz='UTC'),
        'avg_shortwave_radiation': np.random.rand(24) * 1000,
        'avg_wind_speed_10m': np.random.rand(24) * 20,
        'avg_cloud_cover': np.random.rand(24) * 100,
        'avg_temperature_2m': np.random.rand(24) * 30,
        'avg_diffuse_radiation': np.random.rand(24) * 500,
        'solar_generation': np.random.rand(24) * 7000,
        'wind_generation_on': np.random.rand(24) * 30000,
        'wind_generation_off': np.random.rand(24) * 8000,
        'avg_wind_speed_10m_off': np.random.rand(24) * 20,
    })
@pytest.fixture
def dummy_capacity():
    return pd.DataFrame({
        'time_stamp': pd.to_datetime(['2023-01-01']),
        'solar_generation_capacity': [63000.0],
        'wind_generation_on_capacity': [58000.0],
        'wind_generation_off_capacity': [8000.0],
    })

def test_build_features(dummy_df,dummy_capacity):
    X, y = build_features(dummy_df, dummy_capacity)
    
    assert X.values.shape == (24, 12)
    assert y.values.shape == (24, 4)
    
    assert not X.isnull().any().any()
    assert not y.isnull().any().any()
    
    sin_cos_cols = [c for c in X.columns if 'sin' in c or 'cos' in c]
    assert X[sin_cos_cols].apply(lambda col: col.between(-1, 1)).all().all()

    assert list(y.columns) == ['solar_generation', 'wind_generation_on', 'wind_generation_off', 'renewable_total_mw']
    
def test_build_sequences(dummy_df, dummy_capacity):
    X, y = build_features(dummy_df, dummy_capacity)
    window_size = 4

    X_seq, y_seq = build_sequences(X.values, y.values, window_size)
    n_samples = len(X) - window_size
    assert X_seq.shape == (n_samples, window_size, 12)
    assert y_seq.shape == (n_samples, 4)