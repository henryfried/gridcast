import numpy as np
import pandas as pd

import matplotlib.pyplot as plt 
from models.evaluate import evaluate

def plot_net_load(prediction, y_test, pred_timestamps, test_timestamps, time_window):
    """Plot predicted vs actual renewable generation for a single model over a time window.

    Args:
        prediction: Array (n_samples, 4) — model predictions [Solar, Wind On, Wind Off, Total].
        y_test: Array (n_samples, 4) — ground truth values.
        pred_timestamps: Timestamps aligned to prediction rows.
        test_timestamps: Timestamps aligned to y_test rows.
        time_window: Tuple (start, end) ISO strings, e.g. ("2024-01-01", "2024-02-01").

    Returns:
        matplotlib Figure with 2x2 subplots (Solar, Wind On, Wind Off, Renewable Total).
    """
    # Mask both arrays to the requested time window
    window_mask_test = (test_timestamps >= np.datetime64(time_window[0])) & (test_timestamps < np.datetime64(time_window[1]))
    window_mask = (pred_timestamps >= np.datetime64(time_window[0])) & (pred_timestamps < np.datetime64(time_window[1]))

    # Slice each target column from predictions and actuals
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


def plot_comparison(model_names, predictions, y_test, test_timestamps, time_window):
    """Overlay predictions from multiple models against actuals for a given time window.

    Args:
        model_names: List of model name strings.
        predictions: Dict {model_name: (pred_array, pred_timestamps)}.
        y_test: Array (n_samples, 4) — ground truth values.
        test_timestamps: Timestamps aligned to y_test rows.
        time_window: Tuple (start, end) ISO strings.

    Returns:
        matplotlib Figure with 2x2 subplots, one line per model plus actuals.
    """
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
            # Only plot actuals once (on the first model iteration)
            if i == 0:
                ax.plot(hours_test, actual, label='Actual')
                ax.set_title(title)
            ax.plot(hours, pred, label=f'{model}', linestyle='--')
            ax.legend()

    return fig


def plot_model_eval(model_names, predictions, y_test_values, test_timestamps):
    """Bar chart comparing RMSE, MAE, and R2 across models and targets.

    Args:
        model_names: List of model name strings.
        predictions: Dict {model_name: (pred_array, pred_timestamps)}.
        y_test_values: Array (n_samples, 4) — full ground truth values.
        test_timestamps: Timestamps aligned to y_test_values rows.

    Returns:
        matplotlib Figure with 3 subplots (one per metric), grouped bars per target.
    """
    fig, axes = plt.subplots(3, 1, figsize=(8, 8))

    error_types = ['RMSE', 'MAE', 'R2']
    model_errors = {}
    for model in model_names:
        # Align y_test rows to the model's prediction timestamps
        mask = np.isin(test_timestamps, predictions[model][1])
        y_test = y_test_values[mask]
        model_errors[model] = evaluate(predictions[model][0], y_test)

    # Compute bar positions so grouped bars don't overlap
    barWidth = 0.5/len(model_errors)
    brs = [np.arange(len(y_test[0]))]
    for _ in range(len(model_errors)-1):
        brs.append([x + barWidth for x in brs[-1]])

    colors = [plt.cm.tab10(i) for i in range(len(model_names))]
    for ax, err_type in zip(axes.flat, error_types):
        ax.set_title(err_type)
        for model_ind, (key, value) in enumerate(model_errors.items()):
            ax.bar(brs[model_ind], value[err_type], color=colors[model_ind], width=barWidth,
                edgecolor='grey', label=key)
        # Centre tick labels between the first and last bar group
        ax.set_xticks((np.array(brs[0])+np.array(brs[-1]))/2, ['Solar', 'Wind on', 'Wind off', 'total'])

    # Single shared legend above all subplots
    handles, labels = axes.flat[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='upper center', bbox_to_anchor=(0.5, 1.02), ncol=len(model_names))
    plt.tight_layout(rect=[0, 0, 1, 0.95])

    return fig