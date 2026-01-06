import pandas as pd
import numpy as np
import torch
import torch.nn as nn
from sklearn.preprocessing import StandardScaler
import joblib
import json

DATA_PATH = "data/subsetA.csv"
MODEL_PATH = "models/autoencoder.pt"
SCALER_PATH = "models/ae_scaler.joblib"
FEATURES_PATH = "models/ae_features.json"

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print("Using device:", DEVICE)

df = pd.read_csv(DATA_PATH)
label_col = df.columns[-1]

df_normal = df[df[label_col] == 0]

X = df_normal.select_dtypes(include=[np.number])

print("Training rows:", X.shape[0])
print("Features:", X.shape[1])

X = X.sample(n=min(50000, len(X)), random_state=42)
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
joblib.dump(scaler, SCALER_PATH)
json.dump(list(X.columns), open(FEATURES_PATH, "w"))
X_tensor = torch.tensor(X_scaled, dtype=torch.float32).to(DEVICE)

class AutoEncoder(nn.Module):
    def __init__(self, input_dim):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 16)
        )
        self.decoder = nn.Sequential(
            nn.Linear(16, 32),
            nn.ReLU(),
            nn.Linear(32, input_dim)
        )

    def forward(self, x):
        z = self.encoder(x)
        return self.decoder(z)

model = AutoEncoder(X.shape[1]).to(DEVICE)
criterion = nn.MSELoss()
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

EPOCHS = 20
BATCH_SIZE = 128

for epoch in range(EPOCHS):
    perm = torch.randperm(X_tensor.size(0))
    total_loss = 0

    for i in range(0, X_tensor.size(0), BATCH_SIZE):
        batch = X_tensor[perm[i:i+BATCH_SIZE]]

        optimizer.zero_grad()
        recon = model(batch)
        loss = criterion(recon, batch)
        loss.backward()
        optimizer.step()

        total_loss += loss.item()

    print(f"Epoch {epoch+1}/{EPOCHS} | Loss: {total_loss:.6f}")

torch.save(model.state_dict(), MODEL_PATH)
print("Model saved to:", MODEL_PATH)
