from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.multioutput import MultiOutputRegressor

from models.features import build_features
from models.utils import load_df, load_capacity, scale_features, scale_targets

def get_model(model_type: str, **kwargs):
    if model_type == 'linear':
        return LinearRegression()
    elif model_type == 'random_forest':
        return RandomForestRegressor(
            n_estimators=kwargs.get('n_estimators', 100),
            max_depth=kwargs.get('max_depth', 15),
            min_samples_leaf=kwargs.get('min_samples_leaf', 10),
            n_jobs=kwargs.get('n_jobs', -1),
            random_state=kwargs.get('random_state', 42)
        )
    elif model_type == 'gradient_boosting':
        return MultiOutputRegressor(GradientBoostingRegressor(
            n_estimators=kwargs.get('n_estimators', 100),
            learning_rate=kwargs.get('learning_rate', 0.05),
            max_depth=kwargs.get('max_depth', 5),
            min_samples_leaf=kwargs.get('min_samples_leaf', 10),
            random_state=kwargs.get('random_state', 42)
        ))

def train(model_type: str, db_name: str, train_years: list[int], test_years: list[int], **kwargs):
    train_df = load_df(db_name, train_years)
    test_df = load_df(db_name, test_years)
    
    train_capacity = load_capacity(train_years)
    test_capacity = load_capacity(test_years)
    
    X_train, y_train = build_features(train_df, train_capacity)
    X_test, y_test = build_features(test_df, test_capacity)
    
    test_timestamps = test_df["hourly"].values
    
    X_train_scaled, x_scaler = scale_features(X_train)
    X_test_scaled = x_scaler.transform(X_test)
    y_train_scaled, y_scaler  = scale_targets(y_train)
    
    model = get_model(model_type, **kwargs)
    print(f"Training {model_type}...")
    model.fit(X_train_scaled, y_train_scaled)
    print("Done.")
    predictions = model.predict(X_test_scaled)
    pred_scaled = y_scaler.inverse_transform(predictions)

    return model, pred_scaled, y_test.values, test_timestamps

    

