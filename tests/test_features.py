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

def _dummy_weather_columns(n):
    return {
        'avg_shortwave_radiation': np.random.rand(n) * 1000,
        'avg_wind_speed_10m': np.random.rand(n) * 20,
        'avg_cloud_cover': np.random.rand(n) * 100,
        'avg_temperature_2m': np.random.rand(n) * 30,
        'avg_diffuse_radiation': np.random.rand(n) * 500,
        'solar_generation': np.random.rand(n) * 7000,
        'wind_generation_on': np.random.rand(n) * 30000,
        'wind_generation_off': np.random.rand(n) * 8000,
        'avg_wind_speed_10m_off': np.random.rand(n) * 20,
    }

def _dummy_capacity(year):
    return pd.DataFrame({
        'time_stamp': pd.to_datetime([f'{year}-01-01']),
        'solar_generation_capacity': [63000.0],
        'wind_generation_on_capacity': [58000.0],
        'wind_generation_off_capacity': [8000.0],
    })

@pytest.fixture
def dummy_df():
    return pd.DataFrame({
        'hourly': pd.date_range('2023-01-01', periods=24, freq='h', tz='UTC'),
        **_dummy_weather_columns(24),
    })
@pytest.fixture
def dummy_capacity():
    return _dummy_capacity(2023)

def test_build_features(dummy_df,dummy_capacity):
    X, y = build_features(dummy_df, dummy_capacity)
    
    assert X.values.shape == (24, 12)
    assert y.values.shape == (24, 4)
    
    assert not X.isnull().any().any()
    assert not y.isnull().any().any()
    
    sin_cos_cols = [c for c in X.columns if 'sin' in c or 'cos' in c]
    assert X[sin_cos_cols].apply(lambda col: col.between(-1, 1)).all().all()

    assert list(y.columns) == ['solar_generation', 'wind_generation_on', 'wind_generation_off', 'renewable_total_capacity_factor']

@pytest.mark.parametrize("year,days_in_year", [(2024, 366), (2023, 365)])
def test_build_features_day_of_year_period_matches_year_length(year, days_in_year):
    """
    Regression test for the hardcoded period=356 bug in build_features.

    1. Build a daily-frequency dataframe spanning exactly one full calendar
       year (`days_in_year` rows), so the last row is always the final day
       of that year (day_of_year == days_in_year).
    2. Run build_features, which picks the cyclical period per row from
       is_leap_year (365, or 366 in a leap year) instead of a fixed constant.
    3. Assert the last row's day_of_year really is days_in_year, so the
       assertion below is checking what it claims to check.
    4. Assert day_of_year_sin/cos for that last row equal (0, 1): the angle
       2*pi * days_in_year / period only reduces to exactly 2*pi (wrapping
       back to zero) when period truly equals days_in_year for that row.
       The old hardcoded period=356 would produce a different, wrong angle.
    5. Parametrized over a leap year (2024, 366 days) and a non-leap year
       (2023, 365 days), so the fix is proven for both period values, not
       just one that might coincidentally match a hardcoded constant.
    """
    df = pd.DataFrame({
        'hourly': pd.date_range(f'{year}-01-01', periods=days_in_year, freq='D', tz='UTC'),
        **_dummy_weather_columns(days_in_year),
    })
    capacity_df = _dummy_capacity(year)

    X, _ = build_features(df, capacity_df)

    assert df['hourly'].iloc[-1].day_of_year == days_in_year
    assert X['day_of_year_sin'].iloc[-1] == pytest.approx(0, abs=1e-6)
    assert X['day_of_year_cos'].iloc[-1] == pytest.approx(1, abs=1e-6)

def test_build_features_zero_capacity_does_not_poison_combined_total():
    """
    Regression test: a single technology with zero capacity in a year must
    not turn renewable_total_capacity_factor into NaN for that whole year,
    even though its own individual capacity-factor column correctly is NaN
    (undefined - there's no such thing as a capacity factor for a technology
    with no capacity).

    Builds one year where wind_generation_off_capacity is 0 (as if offshore
    wind didn't exist yet) while solar and onshore capacity are valid, then
    checks wind_generation_off (the individual target) is NaN as expected,
    but renewable_total_capacity_factor is not - solar and onshore alone
    still produce a valid combined figure.
    """
    n = 5
    df = pd.DataFrame({
        'hourly': pd.date_range('2010-01-01', periods=n, freq='D', tz='UTC'),
        **_dummy_weather_columns(n),
    })
    capacity_df = pd.DataFrame({
        'time_stamp': pd.to_datetime(['2010-01-01']),
        'solar_generation_capacity': [63000.0],
        'wind_generation_on_capacity': [58000.0],
        'wind_generation_off_capacity': [0.0],
    })

    _, y = build_features(df, capacity_df)

    assert y['wind_generation_off'].isnull().all()
    assert not y['renewable_total_capacity_factor'].isnull().any()
    assert (y['renewable_total_capacity_factor'] <= 1.0).all()

def test_build_features_combined_total_excludes_generation_from_unknown_capacity():
    """
    Regression test: a technology's generation must be excluded from
    renewable_total_capacity_factor's numerator whenever its capacity is
    excluded from the denominator - otherwise generation from a technology
    with no counted capacity gets credited for free, and the combined
    ratio can exceed 1 (physically impossible for a capacity factor).

    Uses fixed (not random) generation/capacity values so the expected
    combined ratio can be computed exactly: despite offshore reporting
    large generation, its capacity is zero/unknown, so the combined total
    must equal solar+onshore generation over solar+onshore capacity only.
    """
    n = 3
    weather_only = {k: v for k, v in _dummy_weather_columns(n).items()
                    if k not in ('solar_generation', 'wind_generation_on', 'wind_generation_off')}
    df = pd.DataFrame({
        'hourly': pd.date_range('2010-01-01', periods=n, freq='D', tz='UTC'),
        **weather_only,
        'solar_generation': np.full(n, 100.0),
        'wind_generation_on': np.full(n, 100.0),
        'wind_generation_off': np.full(n, 5000.0),  # large, despite zero capacity below
    })
    capacity_df = pd.DataFrame({
        'time_stamp': pd.to_datetime(['2010-01-01']),
        'solar_generation_capacity': [1000.0],
        'wind_generation_on_capacity': [1000.0],
        'wind_generation_off_capacity': [0.0],
    })

    _, y = build_features(df, capacity_df)

    expected = (100.0 + 100.0) / (1000.0 + 1000.0)
    assert y['renewable_total_capacity_factor'].values == pytest.approx(expected)
    assert (y['renewable_total_capacity_factor'] <= 1.0).all()

def test_build_features_handles_non_default_df_index():
    """
    Regression test: build_features must not silently misalign when df has
    a non-default index (e.g. a caller filtered/sliced it upstream).

    pd.merge always resets capacity_matched to a fresh 0..n-1 index; if df
    keeps a different index, index-aligned arithmetic between df and
    capacity_matched unions the two disjoint index sets instead of matching
    rows - producing a wrong-shaped, all-NaN result with no error at all.
    """
    n = 5
    df = pd.DataFrame({
        'hourly': pd.date_range('2023-01-01', periods=n, freq='D', tz='UTC'),
        **_dummy_weather_columns(n),
    })
    df.index = range(10, 10 + n)  # non-default index, e.g. post-filter/slice
    capacity_df = _dummy_capacity(2023)

    X, y = build_features(df, capacity_df)

    assert X.shape[0] == n
    assert y.shape[0] == n
    assert not y.isnull().any().any()

def test_build_features_all_capacity_zero_gives_nan_combined_total():
    """
    Companion regression test: if *every* technology has zero capacity in a
    year (fully degenerate case), renewable_total_capacity_factor must still
    be NaN - a 0/0 combined ratio is genuinely undefined and must not
    silently resolve to some other value (e.g. 0 or inf).
    """
    n = 5
    df = pd.DataFrame({
        'hourly': pd.date_range('2010-01-01', periods=n, freq='D', tz='UTC'),
        **_dummy_weather_columns(n),
    })
    capacity_df = pd.DataFrame({
        'time_stamp': pd.to_datetime(['2010-01-01']),
        'solar_generation_capacity': [0.0],
        'wind_generation_on_capacity': [0.0],
        'wind_generation_off_capacity': [0.0],
    })

    _, y = build_features(df, capacity_df)

    assert y['renewable_total_capacity_factor'].isnull().all()

def test_build_sequences(dummy_df, dummy_capacity):
    X, y = build_features(dummy_df, dummy_capacity)
    window_size = 4

    X_seq, y_seq = build_sequences(X.values, y.values, window_size)
    n_samples = len(X) - window_size
    assert X_seq.shape == (n_samples, window_size, 12)
    assert y_seq.shape == (n_samples, 4)