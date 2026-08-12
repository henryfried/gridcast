from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.multioutput import MultiOutputRegressor

from models.features import build_features
from models.utils import load_capacity, load_df, scale_features, scale_targets, check_quantile_crossing

import numpy as np

def get_model(model_type: str, quantile_alpha: float | None = None, **kwargs):
    """
    Build an untrained model instance for the given model_type.

    Parameters
    ----------
    model_type : str
        One of "linear", "random_forest", "gradient_boosting".
    quantile_alpha : float, optional
        Only affects "gradient_boosting": if truthy, switches the GBM to
        quantile loss at this alpha instead of squared-error loss. Leave
        as None for a standard point-prediction model.

    Returns
    -------
    estimator
        An untrained sklearn estimator (LinearRegression, RandomForestRegressor,
        or a MultiOutputRegressor wrapping GradientBoostingRegressor).
    """
    if quantile_alpha is not None and model_type != 'gradient_boosting':
        raise ValueError(f"quantile_alpha is only supported for gradient_boosting, got model_type={model_type!r}")
    
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
        quantile_kwargs = {}
        if quantile_alpha is not None:
            quantile_kwargs= {
            "loss": 'quantile',
            "alpha": quantile_alpha
            }
        return MultiOutputRegressor(GradientBoostingRegressor(
            n_estimators=kwargs.get('n_estimators', 100),
            learning_rate=kwargs.get('learning_rate', 0.05),
            max_depth=kwargs.get('max_depth', 5),
            min_samples_leaf=kwargs.get('min_samples_leaf', 10),
            random_state=kwargs.get('random_state', 42),
            **quantile_kwargs,
        ))

def prepare_data(db_name, train_years, test_years):
    """
    Load, feature-build, and scale train/test data for a db view/table and year ranges.

    Parameters
    ----------
    db_name : str
        Table or view name to query (e.g. "v_weather_generation").
    train_years : list[int]
        [year] for a single year, or [start_year, end_year] for a range.
    test_years : list[int]
        Same format as train_years.

    Returns
    -------
    tuple
        (X_train_scaled, X_test_scaled, y_train_scaled, y_test, y_scaler,
        test_timestamps). y_test and test_timestamps are NOT scaled: y_test
        is the raw build_features() output, kept in original units so it's
        ready to compare against inverse-transformed predictions.
    """
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
    return X_train_scaled, X_test_scaled, y_train_scaled, y_test, y_scaler, test_timestamps 
    
def train(model_type: str, db_name: str, train_years: list[int], test_years: list[int], **kwargs):
    """
    Train a single point-prediction model and predict on the test set.

    Parameters
    ----------
    model_type : str
        Passed straight through to get_model (see there for options).
    db_name : str
        Table or view name to query.
    train_years : list[int]
        [year] for a single year, or [start_year, end_year] for a range.
    test_years : list[int]
        Same format as train_years.

    Returns
    -------
    tuple
        (model, pred_scaled, y_test_values, test_timestamps). Despite the
        name, pred_scaled is already inverse_transform'd back to original
        units, not the scaled/normalized model output.
    """
    X_train_scaled, X_test_scaled, y_train_scaled, y_test, y_scaler, test_timestamps = prepare_data(db_name, train_years, test_years)

    model = get_model(model_type, **kwargs)
    print(f"Training {model_type}...")
    model.fit(X_train_scaled, y_train_scaled)
    print("Done.")
    predictions = model.predict(X_test_scaled)
    pred_scaled = y_scaler.inverse_transform(predictions)

    return model, pred_scaled, y_test.values, test_timestamps



def train_quantile_gbm(model_type: str, db_name: str, train_years: list[int], test_years: list[int], quantile_alphas: list[float], **kwargs):
    """
    Train one independent GBM per quantile alpha, then rearrange to fix any crossing.

    Each alpha gets its own separately-fit model (see get_model): nothing
    ties them together during training, so crossing is expected and fixed
    post-hoc via check_quantile_crossing rather than prevented structurally.

    Parameters
    ----------
    model_type : str
        Passed straight through to get_model on each iteration.
    db_name : str
        Table or view name to query.
    train_years : list[int]
        [year] for a single year, or [start_year, end_year] for a range.
    test_years : list[int]
        Same format as train_years.
    quantile_alphas : list[float]
        Quantile levels to train, e.g. [0.1, 0.5, 0.9]. Order doesn't
        matter on input: sorted ascending below before use.

    Returns
    -------
    tuple
        (models, preds_raw_scaled, preds_sorted, y_test_values, test_timestamps).
        models/preds_raw_scaled/preds_sorted are all keyed by f"quantile_{alpha}".
        preds_raw_scaled is the raw (possibly crossing) per-model output;
        preds_sorted is the same after check_quantile_crossing.
    """
    X_train_scaled, X_test_scaled, y_train_scaled, y_test, y_scaler, test_timestamps = prepare_data(db_name, train_years, test_years)
    models = {}
    preds_raw_scaled ={}
    # ascending order matters: check_quantile_crossing compares adjacent
    # alphas pairwise, and callers slice preds by position assuming this order
    quantile_alphas_sorted = np.sort(np.array(quantile_alphas))
    for alpha in quantile_alphas_sorted:
        model = get_model(model_type,alpha, **kwargs)
        print(f"Training {model_type} for quantile alpha = {alpha}...")
        model.fit(X_train_scaled, y_train_scaled)
        print("Done.")
        predictions = model.predict(X_test_scaled)
        pred_scaled = y_scaler.inverse_transform(predictions)
        models[f'quantile_{alpha}'] = model
        preds_raw_scaled[f'quantile_{alpha}'] = pred_scaled

    preds_sorted = check_quantile_crossing(preds_raw_scaled, quantile_alphas_sorted)


    return models, preds_raw_scaled, preds_sorted, y_test.values, test_timestamps
