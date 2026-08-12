import torch
from torch import nn, optim
import numpy as np

from models.utils import prepare_data, check_quantile_crossing

class MLP(nn.Module):
    """
    Feedforward net for point prediction, or quantile prediction via
    separate output heads sharing one trunk.

    Parameters
    ----------
    layer_dims : list[int]
        Trunk layer sizes, e.g. [12, 64, 128, 64]: input dim first, each
        hidden layer's width after that.
    n_targets : int
        Number of targets predicted per quantile (or per row, in point mode).
    dropout_rate : float
        Dropout probability applied after every trunk layer.
    qunatile_alphas : list[float] or None
        One output head is created per entry - only the count matters here,
        not the values (see train_neural for where values get attached to
        a head). None/empty gives a single point-prediction head instead.
    """
    def __init__(self, layer_dims: list, n_targets: int, dropout_rate: float, quantile_alphas: list[float]) -> None:
        super().__init__()
        self.is_quantile = False
        layers = []
        for dim in range(len(layer_dims)-1):
            layers.append(nn.Linear(layer_dims[dim], layer_dims[dim+1]))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(p=dropout_rate))
        self.model = nn.Sequential(*layers)

        if quantile_alphas:
            self.is_quantile = True
            self.heads = nn.ModuleList()
            for _ in quantile_alphas:
                self.heads.append(nn.Linear(layer_dims[-1], n_targets))
        else:
            self.linear = nn.Linear(layer_dims[-1], n_targets)
        
    def forward(self, x):
        """Return a single tensor in point mode, or a list of tensors (one per
        quantile head, same order as qunatile_alphas) in quantile mode - callers
        must branch on self.is_quantile, not assume a single tensor either way."""
        x = self.model(x)
        if self.is_quantile:
            return [head(x) for head in self.heads]
        else:
            return self.linear(x)

def pinball_loss(y_pred, y_true, alpha):
    """Pinball (quantile) loss: max(alpha*diff, (alpha-1)*diff) for
    diff = y_true - y_pred. Asymmetric by design - under- and over-prediction
    are penalized differently depending on alpha, which is what makes
    minimizing it target a specific quantile rather than the mean."""
    diff = y_true - y_pred
    return torch.max(alpha * diff, (alpha - 1) * diff).mean()


def train_neural(db_name: str, train_years: list[int], valid_years: list[int], test_years: list[int], **kwargs):
    """
    Train one MLP - point prediction, or joint multi-quantile prediction via
    separate heads with a summed pinball loss - and predict on the test set.

    Unlike train_quantile_gbm's independent per-alpha models, this is ONE
    model trained jointly: gradients from every quantile's pinball loss flow
    through the same shared trunk every batch.

    Parameters
    ----------
    db_name : str
        Table or view name to query.
    train_years : list[int]
        [year] for a single year, or [start_year, end_year] for a range.
    valid_years : list[int]
        Same format as train_years. Held out for early stopping - unlike
        the GBM path, this model needs its own validation split.
    test_years : list[int]
        Same format as train_years.
    **kwargs
        layer_dims, batch_size, n_targets, n_epochs, lr, patience,
        dropout_rate, min_delta: see their defaults below.
        quantile_alphas : list[float] or None
            None/omitted trains a single point-prediction head (MSE loss).
            Given a list, trains one head per alpha jointly (pinball loss),
            then rearranges via check_quantile_crossing before returning.

    Returns
    -------
    tuple
        (model, pred_scaled, y_test, train_loss, valid_loss, test_timestamps).
        In quantile mode, pred_scaled is a dict keyed by f"quantile_{alpha}"
        (same convention as train_quantile_gbm); otherwise a single array.
        y_test is the raw build_features() DataFrame, not converted to
        .values here (unlike train()/train_quantile_gbm in models/train.py).
    """
    layer_dims = kwargs.get('layer_dims', [12, 64, 128, 64])
    batch_size=kwargs.get('batch_size', 256)
    n_targets = kwargs.get('n_targets', 4)
    n_epochs = kwargs.get('n_epochs', 100)
    lr = kwargs.get('lr', 1e-3)
    patience = kwargs.get('patience', 10)
    dropout_rate = kwargs.get('dropout_rate', 0.2)
    min_delta = kwargs.get('min_delta', 1e-4)
    quantile_alphas = kwargs.get('quantile_alphas', None)
    
    train_loader, valid_loader, X_test_scaled, y_test, y_scaler, test_timestamps  = prepare_data(db_name, train_years, valid_years, test_years, batch_size, seq_len=0)
    if quantile_alphas is not None:
        quantile_alphas_sorted = np.sort(np.array(quantile_alphas))

    model = MLP(layer_dims, n_targets, dropout_rate, quantile_alphas)
    loss_fn = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=lr)
    train_loss = []
    valid_loss = []
    best_val_loss = float('inf')
    patience_counter = 0
    best_weights = None
    
    for epoch in range(n_epochs):
        epoch_train_loss = 0
        epoch_valid_loss = 0
        train_batch = 0
        valid_batch = 0

        model.train()
        for X_batch, y_batch in train_loader:
            optimizer.zero_grad()
            y_pred = model(X_batch)

            if quantile_alphas:
                loss = 0
                for ind, alpha in enumerate(quantile_alphas_sorted):
                    loss +=  pinball_loss(y_pred[ind], y_batch, alpha)
            else:
                loss = loss_fn(y_pred, y_batch)

            loss.backward()
            optimizer.step()
            
            epoch_train_loss += loss
            train_batch += 1
    
            
        model.eval()
       
        with torch.no_grad():
            for X_batch, y_batch in valid_loader:    
                y_pred = model(X_batch)
                if quantile_alphas:
                    loss = 0
                    for ind, alpha in enumerate(quantile_alphas_sorted):
                        loss +=  pinball_loss(y_pred[ind], y_batch, alpha)
                else:
                    loss = loss_fn(y_pred, y_batch)
                epoch_valid_loss += loss
                valid_batch += 1
                

        train_loss.append((epoch_train_loss / train_batch).detach().item())
        valid_loss.append((epoch_valid_loss / valid_batch).detach().item())
        
        if valid_loss[-1] < best_val_loss - min_delta:
            best_val_loss = valid_loss[-1]
            patience_counter = 0
            best_weights = model.state_dict().copy()
        else:
            patience_counter += 1
            if patience_counter >= patience:
                print(f"Early stopping at epoch {epoch+1}")
                model.load_state_dict(best_weights)
                break
  
        print(f"Epoch {epoch+1:4d}/{n_epochs} — train loss: {epoch_train_loss/train_batch:.4f} — val loss: {epoch_valid_loss/valid_batch:.4f}")

    model.eval()
    if quantile_alphas:
        predictions = model(torch.tensor(X_test_scaled, dtype=torch.float32))
        preds_raw_scaled = {}
        for alpha, pred in zip(quantile_alphas_sorted, predictions):
            preds_raw_scaled[f"quantile_{alpha}"] = y_scaler.inverse_transform(pred.detach().numpy())
        pred_scaled = check_quantile_crossing(preds_raw_scaled, quantile_alphas_sorted)

    else:
        predictions = model(torch.tensor(X_test_scaled, dtype=torch.float32)).detach().numpy()
        pred_scaled = y_scaler.inverse_transform(predictions)

    return model, pred_scaled, y_test, train_loss, valid_loss, test_timestamps
