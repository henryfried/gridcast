import streamlit as st
import pandas as pd
import numpy as np
import datetime
import os
import warnings
warnings.filterwarnings("ignore")

from ingestion.utils import engine
from models.persistence import load_model, load_predictions
from models.utils import load_df
from models.features import build_features
from models.plot import plot_net_load, plot_comparison, plot_model_eval
from models.evaluate import evaluate


model_names_selectbox = st.sidebar.multiselect(
    'Chose model',
    ('linear_regression', 'random_forest', 'gradient_boosting', 'mlp', 'transformer')
)

date_time_slider = st.sidebar.slider(
    'Timestamps',
    min_value=datetime.date(2024, 1, 1),
    max_value=datetime.date(2024, 12, 30),
    value=(datetime.date(2024, 6, 16), datetime.date(2024, 6, 17))
)

@st.cache_data
def load_predictions_app():
    predictions = {}
    for f in os.listdir('artifacts/predictions'):
        if f.endswith('.npz'):
            model_name = f.replace('.npz', '')
            predictions[model_name] = load_predictions(f'artifacts/predictions/{f}')
    
    return predictions

@st.cache_data
def load_test():
    test_df = load_df('v_forecast_features', [2024])
    _, y_test = build_features(test_df)
    test_timestamps = pd.to_datetime(test_df["hourly"].values).values
    return y_test, test_timestamps
    
predictions  = load_predictions_app()
y_test, test_timestamps = load_test()

for model in model_names_selectbox:
    fig = plot_net_load(predictions[model][0], y_test.values, pd.to_datetime(predictions[model][1]).values, test_timestamps, [str(date_time_slider[0]), str(date_time_slider[1])])
    st.pyplot(fig)

if model_names_selectbox:
    fig_comparison = plot_comparison(model_names_selectbox, predictions, y_test.values, test_timestamps, [str(date_time_slider[0]), str(date_time_slider[1])])
    st.pyplot(fig_comparison)
 

    
