import torch
from torch import nn, optim
from torch.utils.data import DataLoader, TensorDataset

from models.utils import prepare_data

class MLP(nn.Module):
    def __init__(self, layer_dims: list, out_dim: int, dropout_rate: float) -> None:
        super().__init__()
        
        layers = []
        for dim in range(len(layer_dims)-1):
            layers.append(nn.Linear(layer_dims[dim], layer_dims[dim+1]))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(p=dropout_rate))
        self.model = nn.Sequential(*layers)
        self.linear = nn.Linear(layer_dims[-1], out_dim)
        
    def forward(self, x):
        x = self.model(x)
        return self.linear(x)

def train_neural(db_name: str, train_years: list[int], valid_years: list[int], test_years: list[int], **kwargs):
    layer_dims = kwargs.get('layer_dims', [12, 64, 128, 64])
    batch_size=kwargs.get('batch_size', 256)
    out_dim = kwargs.get('out_dim', 4)
    n_epochs = kwargs.get('n_epochs', 100)
    lr = kwargs.get('lr', 1e-3)
    patience = kwargs.get('patience', 10)
    dropout_rate = kwargs.get('dropout_rate', 0.2)
    min_delta = kwargs.get('min_delta', 1e-4)
    
    
    train_loader, valid_loader, X_test_scaled, y_test, y_scaler, test_timestamps  = prepare_data(db_name, train_years, valid_years, test_years, batch_size, seq_len=0)
    
    
    
    model = MLP(layer_dims, out_dim, dropout_rate)
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
            pred = model(X_batch)
            loss = loss_fn(pred, y_batch)
            loss.backward()
            optimizer.step()
            
            epoch_train_loss += loss
            train_batch += 1
    
            
        model.eval()
       
        with torch.no_grad():
            for X_batch, y_batch in valid_loader:    
                pred = model(X_batch)
                loss = loss_fn(pred, y_batch)
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
    predictions = model(torch.tensor(X_test_scaled, dtype=torch.float32)).detach().numpy()
    pred_scaled = y_scaler.inverse_transform(predictions)

    return model, pred_scaled, y_test, train_loss, valid_loss, test_timestamps