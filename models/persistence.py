import joblib
import torch
import numpy as np

def save_sklearn(model, path: str):
    joblib.dump(model, path)

def load_sklearn(path):
    return joblib.load(path)
    
def save_model(model, path: str):
    torch.save(model.state_dict(), path)   

def load_model(model, path: str):
    model.load_state_dict(torch.load(path, weights_only=True))

def save_predictions(predictions, timestamps, path: str):
    np.savez(path, predictions=predictions, timestamps=timestamps)

def load_predictions(path: str):
    data = np.load(path, allow_pickle=True)
    return data['predictions'], data['timestamps']