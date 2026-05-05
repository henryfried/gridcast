import numpy as np
import pandas as pd

import matplotlib.pyplot as plt 

def plot_net_load(prediction, y_test, test_timestamps, time_window):
    window_mask = (test_timestamps >= np.datetime64(time_window[0])) & (test_timestamps < np.datetime64(time_window[1]))
    solar_pred = prediction[window_mask,0]
    wind_on_pred = prediction[window_mask,1]
    wind_off_pred = prediction[window_mask,2]
    renew_total_pred = prediction[window_mask,3]
    
    solar = y_test[window_mask,0]
    wind_on = y_test[window_mask,1]
    wind_off = y_test[window_mask,2]
    renew_total = y_test[window_mask,3]
    fig, axes = plt.subplots(2, 2, figsize=(14, 8))
    targets = ['Solar', 'Wind On', 'Wind Off', 'Renewable Total']
    actuals = [solar, wind_on, wind_off, renew_total]
    preds = [solar_pred, wind_on_pred, wind_off_pred, renew_total_pred]
    hours = test_timestamps[window_mask]

    for ax, title, actual, pred in zip(axes.flat, targets, actuals, preds):
        ax.plot(hours, actual, label='Actual')
        ax.plot(hours, pred, label='Predicted', linestyle='--')
        ax.set_title(title)
        ax.legend()

    plt.tight_layout()
    plt.show()
    # print(test_time_stamps)


    # window_mask
    # solar = y_test[]
    # print(y_test)
    # solar_pred = prediction['solar_generation']
    
    