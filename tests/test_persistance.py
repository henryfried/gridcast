import numpy as np
from sklearn.linear_model import LinearRegression

from models.persistence import save_model, save_sklearn, save_predictions, load_model, load_sklearn, load_predictions

# TODO: add test for save_model/load_model once MLP fixture is available

def test_save_load_sklearn(tmp_path):
    dummy_model = LinearRegression().fit(np.random.rand(100, 12), np.random.rand(100, 4))
    
    model_path = tmp_path / 'model.joblib'
    save_sklearn(dummy_model, model_path)
    model = load_sklearn(model_path)
    
    X = np.random.rand(10, 12)
    np.testing.assert_array_equal(model.predict(X), dummy_model.predict(X))


def test_save_load_predictions(tmp_path):
    dummy_predictions = np.random.rand(100, 4)
    dummy_timestamps = np.arange(100)
    
    pred_path = tmp_path / 'pred.npz'
    save_predictions(dummy_predictions, dummy_timestamps, pred_path)
    predictions, timestamps = load_predictions(pred_path)
    
    np.testing.assert_array_equal(predictions, dummy_predictions)
    np.testing.assert_array_equal(timestamps, dummy_timestamps)
    
    