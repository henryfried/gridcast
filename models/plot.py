import numpy as np
import pandas as pd

import matplotlib.pyplot as plt 
from models.evaluate import evaluate
def plot_net_load(prediction, y_test, pred_timestamps, test_timestamps, time_window):
    window_mask_test = (test_timestamps >= np.datetime64(time_window[0])) & (test_timestamps < np.datetime64(time_window[1]))
    window_mask = (pred_timestamps >= np.datetime64(time_window[0])) & (pred_timestamps < np.datetime64(time_window[1]))

    solar_pred = prediction[window_mask,0]
    wind_on_pred = prediction[window_mask,1]
    wind_off_pred = prediction[window_mask,2]
    renew_total_pred = prediction[window_mask,3]
    
    solar = y_test[window_mask_test,0]
    wind_on = y_test[window_mask_test,1]
    wind_off = y_test[window_mask_test,2]
    renew_total = y_test[window_mask_test,3]
    fig, axes = plt.subplots(2, 2, figsize=(14, 8))
    targets = ['Solar', 'Wind On', 'Wind Off', 'Renewable Total']
    actuals = [solar, wind_on, wind_off, renew_total]
    preds = [solar_pred, wind_on_pred, wind_off_pred, renew_total_pred]
    hours = pred_timestamps[window_mask]
    hours_test = test_timestamps[window_mask_test]
    for ax, title, actual, pred in zip(axes.flat, targets, actuals, preds):
        ax.plot(hours_test, actual, label='Actual')
        ax.plot(hours, pred, label='Predicted', linestyle='--')
        ax.set_title(title)
        ax.legend()

    plt.tight_layout()
    return fig 


def plot_comparison(model_names, predictions, y_test,test_timestamps, time_window):
    fig, axes = plt.subplots(2, 2, figsize=(14, 8))

    window_mask_test = (test_timestamps >= np.datetime64(time_window[0])) & (test_timestamps < np.datetime64(time_window[1]))

    for i, model in enumerate(model_names):

        preds = predictions[model][0]
        window_mask = (predictions[model][1] >= np.datetime64(time_window[0])) & (predictions[model][1] < np.datetime64(time_window[1]))

        solar_pred = preds[window_mask,0]
        wind_on_pred = preds[window_mask,1]
        wind_off_pred = preds[window_mask,2]
        renew_total_pred = preds[window_mask,3]
        
        solar = y_test[window_mask_test,0]
        wind_on = y_test[window_mask_test,1]
        wind_off = y_test[window_mask_test,2]
        renew_total = y_test[window_mask_test,3]
        
        targets = ['Solar', 'Wind On', 'Wind Off', 'Renewable Total']
        actuals = [solar, wind_on, wind_off, renew_total]
        model_preds = [solar_pred, wind_on_pred, wind_off_pred, renew_total_pred]
        
        hours = predictions[model][1][window_mask]
        hours_test = test_timestamps[window_mask_test]
        
        for ax, title, actual, pred in zip(axes.flat, targets, actuals, model_preds):
            if i == 0:
                ax.plot(hours_test, actual, label='Actual')
                ax.set_title(title)
            ax.plot(hours, pred, label=f'{model}', linestyle='--')
            ax.legend()
            
    return fig
    
def plot_model_eval(model_names, predictions, y_test):
    barWidth = 0.25
    fig, axes = plt.subplots(3, 1, figsize=(14, 8))
    
    # model_error = []
    error_types = ['RMSE', 'MAE', 'R2']
    for i, model in enumerate(model_names):
        model_errors = {model: evaluate(predictions[model][0], y_test) for model in model_names}


 
    brs =[np.arange(len(model_errors))]
    for _ in range(len(model_errors)-1):
        brs.append([x + barWidth for x in brs[-1]])

    colors = plt.cm.tab10(np.linspace(0, 1, len(model_names)))
    for ind, (ax, err_type) in enumerate(zip(axes.flat, error_types)):
        print(ind)

        # plt.bar(brs[ind], err, color =colors[ind], width = barWidth, 
        #         edgecolor ='grey', label =f'{model_names[ind]}') 
    # plt.bar(br2, ECE, color ='g', width = barWidth, 
    #         edgecolor ='grey', label ='ECE') 
    # plt.bar(br3, CSE, color ='b', width = barWidth, 
    #         edgecolor ='grey', label ='CSE') 

    # plt.xlabel('', fontweight ='bold', fontsize = 15) 
    plt.ylabel('Students passed', fontweight ='bold', fontsize = 15) 
    plt.xticks([r + barWidth for r in range(len(model_error))], 
            ['RMSE', 'MSA', 'R2'])

    plt.legend()
    plt.show()
    return fig