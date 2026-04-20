from sklearn.preprocessing import StandardScaler

import pandas as pd
from ingestion.utils import engine

def load_df(db_name: str, years: list[int]):
    if len(years) > 1: 
        return  pd.read_sql(f"SELECT * FROM {db_name} WHERE EXTRACT(year FROM hourly) BETWEEN {years[0]} AND {years[1]}", engine)
    else:
        return  pd.read_sql(f"SELECT * FROM {db_name} WHERE EXTRACT(year FROM hourly) = {years[0]}", engine)

def scale_features(X_train, X_test):
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    return X_train_scaled, X_test_scaled, scaler

def scale_targets(y_train):
    scaler = StandardScaler()
    y_train_scaled = scaler.fit_transform(y_train)
    return y_train_scaled, scaler