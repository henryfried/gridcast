import torch
from torch import nn, optim

import numpy as np

from models.utils import prepare_data


def getPositionEncoding(seq_len, d, n=10000):
    P = np.zeros((seq_len, d))
    for k in range(seq_len):
        for i in np.arange(int(d/2)):
            denominator = np.power(n, 2*i/d)
            P[k, 2*i] = np.sin(k/denominator)
            P[k, 2*i+1] = np.cos(k/denominator)
    return torch.tensor(P, dtype=torch.float32)


class Transformer(nn.Module):
    def __init__(self, 
        n_head: int,
        d_model: int,
        seq_len: int,
        dropout_rate: float) -> None:
        
        super().__init__()
        self.input_proj = nn.Linear(12, d_model)
        self.register_buffer('positional_encoding', getPositionEncoding(seq_len, d_model))
        self.encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,      # embedding dimension
            nhead=n_head,         # number of attention heads
            dim_feedforward=256,  # feedforward layer size
            batch_first=True ,     # input shape: (batch, seq, features)
            dropout=dropout_rate
        )
        self.output_proj = nn.Linear(d_model, 4)

        
    def forward(self, x):
        x = self.input_proj(x) 
        x += self.positional_encoding 
        x = self.encoder_layer(x)         # (batch, 24, d_model)
        x = x[:, -1, :]             # take last token (batch, d_model)
        x = self.output_proj(x)     # (batch, 4)
    
        return x



def train_transformer(db_name: str, train_years: list[int], valid_years: list[int], test_years: list[int], **kwargs):
    batch_size=kwargs.get('batch_size', 256)
    out_dim = kwargs.get('out_dim', 4)
    n_epochs = kwargs.get('n_epochs', 100)
    lr = kwargs.get('lr', 1e-3)
    patience = kwargs.get('patience', 10)
    dropout_rate = kwargs.get('dropout_rate', 0.2)
    seq_len = kwargs.get('seq_len', 24)
    n_head = kwargs.get('n_head', 1 )
    d_model = kwargs.get('d_model', 64)
    min_delta = kwargs.get('min_delta', 1e-4)
    
    

    
    train_loader, valid_loader, X_test_scaled, y_test, y_scaler, test_timestamps  = prepare_data(db_name, train_years, valid_years, test_years, batch_size, seq_len)

    
    
    
    model = Transformer(n_head,
            d_model,
            seq_len,
            dropout_rate)
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