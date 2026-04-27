import torch
from torch import nn, optim
from torch.utils.data import DataLoader, TensorDataset

from models.features import  build_features
from models.utils import load_df, scale_features, scale_targets

class MLP(nn.Module):
    def __init__(self, layer_dims: list, out_dim: int) -> None:
        super().__init__()
        
        layers = []
        for dim in range(len(layer_dims)-1):
            layers.append(nn.Linear(layer_dims[dim], layer_dims[dim+1]))
            layers.append(nn.ReLU())
        self.model = nn.Sequential(*layers)
        self.linear = nn.Linear(layer_dims[-1], out_dim)
    def forward(self, x):
        x = self.model(x)
        return self.linear(x)

def batch(X, y, batch_size):
    X_t = torch.tensor(X, dtype=torch.float32)
    y_t = torch.tensor(y, dtype=torch.float32)
    dataset = TensorDataset(X_t, y_t)
    return DataLoader(dataset, batch_size, shuffle=True)

def train_neural(db_name: str, train_years: list[int], valid_years: list[int], test_years: list[int], **kwargs):
    layer_dims = kwargs.get('layer_dims', [11, 64, 128, 64])
    batch_size=kwargs.get('batch_size', 4)
    out_dim = kwargs.get('out_dim', 4)
    n_epochs = kwargs.get('n_epochs', 100)
    lr = kwargs.get('lr', 1e-3)
    loss_fn = nn.MSELoss()
    
    
    X_train, y_train = build_features(load_df(db_name, train_years))
    X_valid, y_valid = build_features(load_df(db_name, valid_years))
    X_test, y_test = build_features(load_df(db_name, test_years))
    X_train_scaled, x_scaler = scale_features(X_train)
    X_valid_scaled = x_scaler.transform(X_valid)
    X_test_scaled = x_scaler.transform(X_test)
    
    y_train_scaled, y_scaler  = scale_targets(y_train)
    y_valid_scaled = y_scaler.transform(y_valid)
    
    train_loader = batch(X_train_scaled, y_train_scaled, batch_size)
    valid_loader = batch(X_valid_scaled, y_valid_scaled, batch_size)
    
    
    
    #model = get_model(model_type, **kwargs)
    model = MLP(layer_dims, out_dim)
    optimizer = optim.Adam(model.parameters(), lr=lr)
    train_loss = []
    valid_loss = []
    for epoch in range(n_epochs):
        model.train()
        epoch_train_loss = 0
        epoch_valid_loss = 0
        total_batch = 0
        for X_batch, y_batch in train_loader:
            optimizer.zero_grad()
            pred = model(X_batch)
            loss = loss_fn(pred, y_batch)
            loss.backward()
            optimizer.step()
            
            epoch_train_loss += loss
            total_batch += 1
    
            
        model.eval()
       
        total_batch = 0
        with torch.no_grad():
            for X_batch, y_batch in valid_loader:    
                pred = model(X_batch)
                loss = loss_fn(pred, y_batch)
                epoch_valid_loss += loss
                total_batch += 1
                
        train_loss.append((epoch_train_loss / total_batch).detach().item())
        valid_loss.append((epoch_valid_loss / total_batch).detach().item())
        print(f"Epoch {epoch+1}/{n_epochs} — train loss: {epoch_train_loss/total_batch:.4f} — val loss: {epoch_valid_loss/total_batch:.4f}")
    
    model.eval()
    predictions = model(torch.tensor(X_test_scaled, dtype=torch.float32)).detach().numpy()
    pred_scaled = y_scaler.inverse_transform(predictions)

    return model, pred_scaled, y_test, train_loss, valid_loss