from sklearn.linear_model import LinearRegression

from models.features import build_features
from models.utils import load_df, scale_features, scale_targets


def linear_regression(db_name: str, train_years: list[int], test_years: list[int]):
    X_train, y_train = build_features(load_df(db_name, train_years))
    X_test, y_test = build_features(load_df(db_name, test_years))
    X_train_scaled, X_test_scaled, _ = scale_features(X_train, X_test)
    y_train_scaled, y_scaler  = scale_targets(y_train)
    model = LinearRegression()
    print("Training linear regression...")
    model.fit(X_train_scaled, y_train_scaled)
    print("Done.")
    predictions = model.predict(X_test_scaled)
    pred_scaled = y_scaler.inverse_transform(predictions)
    return model, pred_scaled, y_test

