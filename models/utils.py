from sklearn.preprocessing import StandardScaler
import pandas as pd
from ingestion.utils import engine
import torch
from torch.utils.data import DataLoader, TensorDataset

from models.features import build_features, build_sequences

def load_df(db_name: str, years: list[int]):
    if len(years) > 1: 
        return  pd.read_sql(f"SELECT * FROM {db_name} WHERE EXTRACT(year FROM hourly) BETWEEN {years[0]} AND {years[1]}", engine)
    else:
        return  pd.read_sql(f"SELECT * FROM {db_name} WHERE EXTRACT(year FROM hourly) = {years[0]}", engine)

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
    
    X_train, y_train = build_features(train_df)
    X_valid, y_valid = build_features(valid_df)
    X_test, y_test = build_features(test_df)
    
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
