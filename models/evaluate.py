import numpy as np
from sklearn.metrics import root_mean_squared_error, mean_absolute_error, r2_score

def evaluate(prediction, y_test) -> dict:
    return {'RMSE': root_mean_squared_error(y_test.values, prediction, multioutput='raw_values'),
            'MAE': mean_absolute_error(y_test.values, prediction, multioutput='raw_values'),
            'R2': r2_score(y_test.values, prediction, multioutput='raw_values')}

def residual(prediction, y_test) -> np.array:
    return y_test.values - prediction
    
