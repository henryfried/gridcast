import pandas as pd
import torch
from sklearn.preprocessing import StandardScaler
from torch.utils.data import DataLoader, TensorDataset
import numpy as np 

from ingestion.utils import get_engine
from models.features import build_features, build_sequences


def load_df(db_name: str, years: list[int]):
    if len(years) > 1:
        return  pd.read_sql(f"SELECT * FROM {db_name} WHERE EXTRACT(year FROM hourly) BETWEEN {years[0]} AND {years[1]}", get_engine())
    else:
        return  pd.read_sql(f"SELECT * FROM {db_name} WHERE EXTRACT(year FROM hourly) = {years[0]}", get_engine())

def load_capacity(years: list[int]):
    if len(years) > 1:
        return  pd.read_sql(f"SELECT * FROM entso_e_capacity WHERE EXTRACT(year FROM time_stamp) BETWEEN {years[0]} AND {years[1]}", get_engine(), parse_dates=['time_stamp'])
    else:
        return  pd.read_sql(f"SELECT * FROM entso_e_capacity WHERE EXTRACT(year FROM time_stamp) = {years[0]}", get_engine(), parse_dates=['time_stamp'])
    
def scale_features(X_train):
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    return X_train_scaled, scaler

def scale_targets(y_train):
    scaler = StandardScaler()
    y_train_scaled = scaler.fit_transform(y_train)
    return y_train_scaled, scaler

def batch(X, y, batch_size):
    X_t = torch.tensor(X, dtype=torch.float32)
    y_t = torch.tensor(y, dtype=torch.float32)
    dataset = TensorDataset(X_t, y_t)
    return DataLoader(dataset, batch_size, shuffle=True)

def prepare_data(db_name: str, train_years: list[int], valid_years: list[int], test_years: list[int], batch_size: int, seq_len: int):
    train_df = load_df(db_name, train_years)
    valid_df = load_df(db_name, valid_years)
    test_df = load_df(db_name, test_years)
    
    train_capacity = load_capacity(train_years)
    valid_capacity = load_capacity(valid_years)
    test_capacity = load_capacity(test_years)
    
    X_train, y_train = build_features(train_df, train_capacity)
    X_valid, y_valid = build_features(valid_df, valid_capacity)
    X_test, y_test = build_features(test_df, test_capacity)
    
    X_train_scaled, x_scaler = scale_features(X_train)
    X_valid_scaled = x_scaler.transform(X_valid)
    X_test_scaled = x_scaler.transform(X_test)
    y_train_scaled, y_scaler  = scale_targets(y_train)
    y_valid_scaled = y_scaler.transform(y_valid)
    test_timestamps = test_df["hourly"].values[seq_len:]
    
    if seq_len == 0:
        train_loader = batch(X_train_scaled, y_train_scaled, batch_size)
        valid_loader = batch(X_valid_scaled, y_valid_scaled, batch_size)
        return train_loader, valid_loader, X_test_scaled, y_test, y_scaler, test_timestamps
    
    else:
        X_train_seq, Y_train_seq = build_sequences(X_train_scaled, y_train_scaled, seq_len)
        X_valid_seq, Y_valid_seq = build_sequences(X_valid_scaled, y_valid_scaled, seq_len)
        X_test_seq, y_test_seq = build_sequences(X_test_scaled, y_test.values, seq_len)
        
        train_loader = batch(X_train_seq, Y_train_seq, batch_size)
        valid_loader = batch(X_valid_seq, Y_valid_seq, batch_size)
        return train_loader, valid_loader, X_test_seq, y_test_seq, y_scaler, test_timestamps
    
def check_quantile_crossing(preds_raw_scaled, quantile_alphas):
    """
    Detect quantile crossing and fix it via post-hoc monotone rearrangement.

    Each alpha in train_quantile_gbm is fit as an independent model, so
    nothing structurally guarantees e.g. P10 <= P50 <= P90 per row: this
    sorts the predicted quantiles back into order after the fact (safe even
    when nothing crossed, since sorting already-sorted values is a no-op).
    Rearrangement is a known, valid technique, not a hack (Chernozhukov,
    Fernandez-Val & Galichon, 2010).

    Parameters
    ----------
    preds_raw_scaled : dict[str, np.ndarray]
        {f"quantile_{alpha}": predictions}, each array shape (n_samples, n_targets).
    quantile_alphas : list[float]
        Must already be sorted ascending: crossing is checked pairwise in
        that order, and the same order is used to stack/unstack below.

    Returns
    -------
    dict[str, np.ndarray]
        Same shape/keys as preds_raw_scaled, values sorted along the
        quantile axis per (sample, target).
    """
    preds_sorted = {}
    # purely diagnostic: the rearrangement below runs regardless of this check
    crossing_detected = any(
        not (preds_raw_scaled[f'quantile_{quantile_alphas[i]}'] <= preds_raw_scaled[f'quantile_{quantile_alphas[i+1]}']).all()
        for i in range(len(quantile_alphas) - 1)
    )
    if crossing_detected:
        print('WARNING: quantile result are not sorted and will be post processed')

    stacked = np.stack([preds_raw_scaled[f'quantile_{alpha}'] for alpha in quantile_alphas], axis=0)
    # axis=0 is the quantile axis (see stack above): np.sort defaults to the
    # last axis, which would silently sort targets against each other instead
    sorted_preds = np.sort(stacked, axis=0)

    for ind, alpha in enumerate(quantile_alphas):
        preds_sorted[f'quantile_{alpha}'] = sorted_preds[ind]

    return preds_sorted
