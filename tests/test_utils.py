import numpy as np
import pandas as pd
import pytest

from models.utils import scale_features


@pytest.fixture
def dummy_X_train():
    np.random.seed(42)
    return pd.DataFrame(np.random.rand(100, 11) * 100)

@pytest.fixture
def dummy_X_test():
    np.random.seed(0)
    return pd.DataFrame(np.random.rand(20, 11) * 100)


def test_scale_features(dummy_X_train, dummy_X_test):

    X_train_scaled, scale = scale_features(dummy_X_train)
    X_test_scaled = scale.transform(dummy_X_test)
    
    assert X_train_scaled.mean(axis=0) == pytest.approx(np.zeros(11), abs=1e-6)
    assert X_train_scaled.std(axis=0) == pytest.approx(np.ones(11), abs=1e-6)
    
    assert not np.allclose(X_test_scaled.mean(axis=0), np.zeros(11), atol=1e-6)

    
    
