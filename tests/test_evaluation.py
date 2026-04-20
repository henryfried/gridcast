import pandas as pd
import numpy as np
import pytest

from models.evaluate import evaluate, residual

@pytest.fixture
def dummy_y_test():
    return pd.DataFrame(
        np.array([[1, 2, 3, 4]] * 24, dtype=float) ,
        columns=['solar_generation', 'wind_generation_on', 'wind_generation_off', 'renewable_total_mw']
    )
@pytest.fixture
def dummy_predictions(dummy_y_test):
    return dummy_y_test.values.copy()

def test_evaluation(dummy_predictions, dummy_y_test):
    eval = evaluate(dummy_predictions, dummy_y_test)
    
    assert eval['RMSE'].shape == (4,)
    assert eval['MAE'].shape == (4,)
    assert eval['R2'].shape == (4,)

    assert eval['RMSE'] == pytest.approx(np.zeros(4), abs=1e-6)
    assert eval['MAE'] ==  pytest.approx(np.zeros(4), abs=1e-6)
    assert eval['R2'] == pytest.approx(np.ones(4), abs=1e-6)

    
def test_residual(dummy_predictions, dummy_y_test):
    resid = residual(dummy_predictions, dummy_y_test)
    
    assert resid.shape == (24,4)
    
    assert resid == pytest.approx(np.zeros((24,4)), abs=1e-6)