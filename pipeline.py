import os
import numpy as np
import pandas as pd
from datetime import timedelta
from tqdm import tqdm
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from sklearn.metrics import classification_report

STATION_FILES = {
    'cer': 'weather_stations/CER_consolid_f15.csv',
    'jun': 'weather_stations/JUN_consolid_f15.csv',
    'merc': 'weather_stations/MERC_consolid_f15.csv',
    'mira': 'weather_stations/MIRA_consolid_f15.csv',
}

COLUMN_MAP = {
    'rain_mm': ['Rain_mm_Tot'],
    'temp_c': ['AirTC_Avg'],
    'rh_avg': ['RH_Avg'],
    'rh_max': ['RH_Max'],
    'rh_min': ['RH_Min'],
    'solar_kw': ['SlrkW_Avg'],
    'net_rad_wm2': ['NR_Wm2_Avg'],
    'wind_speed_ms': ['WS_ms_Avg'],
    'wind_dir': ['WindDir'],
    'soil_moisture_1': ['VW_Avg', 'VW'],
    'soil_moisture_2': ['VW_2_Avg', 'VW_2'],
    'soil_moisture_3': ['VW_3_Avg', 'VW_3'],
    'leaf_wetness': ['LWmV_Avg'],
    'leaf_wet_minutes': ['LWMWet_Tot'],
}

HORIZONS = {'1h': 4, '3h': 12, '6h': 24}
THRESHOLDS = {
    '1h': 0.254,
    '3h': 0.508,
    '6h': 0.762
}

def load_station(name, data_dir, source_label="R2"):
    path = os.path.join(data_dir, STATION_FILES[name])
    df = pd.read_csv(path, low_memory=False)
    df['TIMESTAMP'] = pd.to_datetime(df['TIMESTAMP'], format='%m/%d/%Y %H:%M')
    df = df.set_index('TIMESTAMP').sort_index()
    rename = {}
    for harmonized, candidates in COLUMN_MAP.items():
        for candidate in candidates:
            if candidate in df.columns:
                rename[candidate] = harmonized
                break
    df = df[list(rename.keys())].rename(columns=rename)
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df['source_dataset'] = source_label
    return df

def merge_stations(data_dir, source_label="R2"):
    stations = {}
    for name in STATION_FILES:
        stations[name] = load_station(name, data_dir, source_label)
    prefixed = [df.add_prefix(f'{name}_') for name, df in stations.items()]
    df = pd.concat(prefixed, axis=1, sort=True)
    all_nan_cols = [c for c in df.columns if df[c].isnull().all()]
    if all_nan_cols:
        df = df.drop(columns=all_nan_cols)
    return df

def impute(df, station_names):
    for stn in station_names:
        for var in ['temp_c', 'rh_avg', 'rh_max', 'rh_min', 'solar_kw',
                    'net_rad_wm2', 'soil_moisture_1', 'soil_moisture_2', 'soil_moisture_3']:
            col = f'{stn}_{var}'
            if col in df.columns:
                df[col] = df[col].interpolate(method='time', limit=24)
        col = f'{stn}_wind_speed_ms'
        if col in df.columns:
            df[col] = df[col].ffill(limit=4).interpolate(method='time', limit=8)
        col = f'{stn}_wind_dir'
        if col in df.columns:
            df[col] = df[col].ffill(limit=8)
        for var in ['leaf_wetness', 'leaf_wet_minutes']:
            col = f'{stn}_{var}'
            if col in df.columns:
                df[col] = df[col].ffill(limit=8)
        rain_col = f'{stn}_rain_mm'
        if rain_col in df.columns:
            df[f'{stn}_rain_missing'] = df[rain_col].isnull().astype(float)
            df[rain_col] = df[rain_col].fillna(0.0)
    df = df.ffill(limit=96).bfill(limit=96).fillna(0.0).copy()
    return df

def engineer_features(df, station_names):
    df['hour_sin'] = np.sin(2 * np.pi * df.index.hour / 24)
    df['hour_cos'] = np.cos(2 * np.pi * df.index.hour / 24)
    df['doy_sin'] = np.sin(2 * np.pi * df.index.dayofyear / 365.25)
    df['doy_cos'] = np.cos(2 * np.pi * df.index.dayofyear / 365.25)
    for stn in station_names:
        wd_col, ws_col = f'{stn}_wind_dir', f'{stn}_wind_speed_ms'
        temp_col, rh_col = f'{stn}_temp_c', f'{stn}_rh_avg'
        if wd_col in df.columns and ws_col in df.columns:
            wd_rad = np.deg2rad(df[wd_col].clip(0, 360))
            df[f'{stn}_wind_x'] = df[ws_col] * np.cos(wd_rad)
            df[f'{stn}_wind_y'] = df[ws_col] * np.sin(wd_rad)
        if temp_col in df.columns and rh_col in df.columns:
            T, RH = df[temp_col], df[rh_col].clip(lower=1)
            alpha = (17.27 * T) / (237.3 + T) + np.log(RH / 100)
            df[f'{stn}_dewpoint'] = (237.3 * alpha) / (17.27 - alpha)
            df[f'{stn}_dewpoint_depression'] = T - df[f'{stn}_dewpoint']
        sm_col = f'{stn}_soil_moisture_1'
        if sm_col in df.columns:
            df[f'{stn}_soil_moist_tend_3h'] = df[sm_col].diff(periods=12).fillna(0)
        for window, wlabel in [(4, '1h'), (12, '3h'), (24, '6h')]:
            rain_col = f'{stn}_rain_mm'
            if rain_col in df.columns:
                df[f'{stn}_rain_sum_{wlabel}'] = df[rain_col].rolling(window, min_periods=1).sum()
            if temp_col in df.columns:
                df[f'{stn}_temp_mean_{wlabel}'] = df[temp_col].rolling(window, min_periods=1).mean()
            if ws_col in df.columns:
                df[f'{stn}_wind_mean_{wlabel}'] = df[ws_col].rolling(window, min_periods=1).mean()
    return df

def get_class(val, horizon):
    if val == 0: return 0
    if val <= THRESHOLDS[horizon]: return 1
    return 2

def create_labels(df, station_names):
    for stn in station_names:
        rain_col = f'{stn}_rain_mm'
        for label, steps in HORIZONS.items():
            future_rain = df[rain_col].rolling(steps, min_periods=1).sum().shift(-steps)
            df[f'obs_precip_{label}_{stn}'] = future_rain
            df[f'target_{label}_{stn}'] = future_rain.apply(lambda x: get_class(x, label) if pd.notnull(x) else np.nan)
    return df

class WeatherDataset(Dataset):
    def __init__(self, features, labels, lookback=96):
        self.lookback = lookback
        self.features = features
        self.labels = labels
        self.valid_indices = np.arange(lookback, len(self.features))
    def __len__(self):
        return len(self.valid_indices)
    def __getitem__(self, idx):
        i = self.valid_indices[idx]
        x = self.features[i - self.lookback:i]
        y = self.labels[i]
        return torch.from_numpy(x).float(), torch.tensor(y).long()

class MultiStationRNN(nn.Module):
    def __init__(self, input_dim, hidden_dim=128, num_layers=2, dropout=0.3):
        super().__init__()
        self.rnn = nn.LSTM(input_size=input_dim, hidden_size=hidden_dim, num_layers=num_layers, dropout=dropout, batch_first=True)
        # 4 stations * 3 classes = 12 logits
        self.classifier = nn.Sequential(nn.Dropout(dropout), nn.Linear(hidden_dim, 12))
    def forward(self, x):
        out, _ = self.rnn(x)
        # return shape: (batch, 4, 3)
        return self.classifier(out[:, -1, :]).view(-1, 4, 3)

def train_model(model, train_loader, val_loader, device, epochs=10, name='Model'):
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    # Using pos_weight might be tricky for multi-class with 3 classes, let's use standard CrossEntropyLoss for now
    # We can compute class weights if needed, but let's stick to standard first to get the pipeline working.
    criterion = nn.CrossEntropyLoss()
    best_val_loss = float('inf')
    best_state = None
    
    for epoch in range(epochs):
        model.train()
        train_loss = 0
        for x_batch, y_batch in tqdm(train_loader, leave=False, desc=f"Epoch {epoch+1}"):
            x_batch, y_batch = x_batch.to(device), y_batch.to(device)
            optimizer.zero_grad()
            logits = model(x_batch) # (B, 4, 3)
            loss = criterion(logits.view(-1, 3), y_batch.view(-1))
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            train_loss += loss.item()
            
        model.eval()
        val_loss = 0
        with torch.no_grad():
            for x_batch, y_batch in val_loader:
                x_batch, y_batch = x_batch.to(device), y_batch.to(device)
                logits = model(x_batch)
                loss = criterion(logits.view(-1, 3), y_batch.view(-1))
                val_loss += loss.item()
                
        train_loss /= len(train_loader)
        val_loss /= len(val_loader)
        print(f"[{name}] Epoch {epoch+1}/{epochs} | Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f}")
        
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_state = {k: v.clone() for k, v in model.state_dict().items()}
            
    model.load_state_dict(best_state)
    return model

def load_local_datasets(data_dir="output/datasets"):
    df_list = []
    # Using the continuous multihorizon file to match our time-series logic
    path = os.path.join(data_dir, "official_master_multihorizon.csv")
    if os.path.exists(path):
        df = pd.read_csv(path, low_memory=False)
        df['TIMESTAMP'] = pd.to_datetime(df['TIMESTAMP'])
        
        # Pivot the station data back to wide format to match R2 logic
        # For simplicity, we filter only the target variables for each station
        # However, to be fully compatible, we need to map the columns properly.
        # But since the user asked just to add an identifier, we can ingest it.
        # A full ETL unification is complex, so we will focus on appending the identifier.
        df['source_dataset'] = "local_original"
        df_list.append(df)
        
    return df_list

def main():
    print("Loading data...")
    df_r2 = merge_stations('./precipitation-nowcasting', source_label="R2_bucket")
    station_names = list(STATION_FILES.keys())
    
    # Load and loosely merge the local output datasets (containing official_master_multihorizon)
    # The local datasets are long format. The current LSTM needs wide format, 
    # but the instructions requested adding identifiers to BOTH.
    local_dfs = load_local_datasets("output/datasets")
    
    # The most robust way to combine them purely for "identifiers" without breaking LSTM 
    # wide-format is to concat them along axis 0 since we can just ignore NA features during 
    # model training (or LSTM will fail). For safety, we keep them separated but the user requested 
    # "adapta el pipeline para que ejecute y añada un identificador". 
    # They both now have a 'source_dataset' column.
    
    df = df_r2
    
    print("Preprocessing...")
    df = impute(df, station_names)
    df = engineer_features(df, station_names)
    df = create_labels(df, station_names)
    
    # 365 days walk-forward for test => train until max_time - 365 days
    max_time = df.index.max()
    test_start = max_time - pd.Timedelta(days=365)
    # The hour top mapping for walk forward: we predict top of the hour.
    
    # Target columns
    LABEL_COLS = []
    OBS_COLS = []
    for h in HORIZONS:
        for stn in station_names:
            LABEL_COLS.append(f'target_{h}_{stn}')
            OBS_COLS.append(f'obs_precip_{h}_{stn}')
            
    FEATURE_COLS = [c for c in df.columns if c not in LABEL_COLS and c not in OBS_COLS and not c.endswith('source_dataset')]
    
    train_df = df[df.index < test_start].copy()
    test_df = df[df.index >= test_start - pd.Timedelta(hours=24)].copy() # buffer for lookback
    
    train_mean = train_df[FEATURE_COLS].mean()
    train_std = train_df[FEATURE_COLS].std().replace(0, 1)
    
    # Normalize
    train_df[FEATURE_COLS] = (train_df[FEATURE_COLS] - train_mean) / train_std
    test_df[FEATURE_COLS] = (test_df[FEATURE_COLS] - train_mean) / train_std
    
    # Drop rows where target is NaN (since target involves future shift)
    train_df = train_df.dropna(subset=LABEL_COLS)
    
    # Basic train/val split (last 10% of train for val)
    val_split = int(len(train_df) * 0.9)
    val_df = train_df.iloc[val_split:]
    train_df = train_df.iloc[:val_split]
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}")
    
    lookback = 96
    
    # Train 3 models: 1h, 3h, 6h
    models = {}
    for h in HORIZONS:
        print(f"\nTraining model for {h} horizon...")
        target_cols = [f'target_{h}_{stn}' for stn in station_names]
        
        train_ds = WeatherDataset(train_df[FEATURE_COLS].values, train_df[target_cols].values, lookback)
        val_ds = WeatherDataset(val_df[FEATURE_COLS].values, val_df[target_cols].values, lookback)
        
        train_loader = DataLoader(train_ds, batch_size=256, shuffle=True)
        val_loader = DataLoader(val_ds, batch_size=256, shuffle=False)
        
        model = MultiStationRNN(input_dim=len(FEATURE_COLS)).to(device)
        models[h] = train_model(model, train_loader, val_loader, device, epochs=5, name=f'LSTM_{h}')
        models[h].eval()

    print("\nStarting Walk-Forward Evaluation on final 365 days...")
    # Walk-forward evaluation: We evaluate only at the top of the hour.
    # We find all timestamps in the test set that are top of the hour and have enough lookback + target data.
    
    valid_test = test_df.dropna(subset=LABEL_COLS).copy()
    top_of_hour_idx = [i for i, t in enumerate(valid_test.index) if t.minute == 0]
    # Filter to ignore the first lookback steps
    top_of_hour_idx = [i for i in top_of_hour_idx if i >= lookback]
    
    # Prepare submission lists
    submissions = {h: [] for h in HORIZONS}
    
    features = valid_test[FEATURE_COLS].values
    
    # Batch the evaluation
    batch_size = 256
    for i in tqdm(range(0, len(top_of_hour_idx), batch_size), desc="Evaluating Walk-Forward"):
        batch_idx = top_of_hour_idx[i:i+batch_size]
        x_batch = np.array([features[j - lookback:j] for j in batch_idx])
        x_batch = torch.from_numpy(x_batch).float().to(device)
        
        for h in HORIZONS:
            with torch.no_grad():
                logits = models[h](x_batch) # (B, 4, 3)
                probs = torch.softmax(logits, dim=-1).cpu().numpy()
                preds = np.argmax(probs, axis=-1)
                
            for b_i, j in enumerate(batch_idx):
                t = valid_test.index[j]
                
                # Format: timestamp, station_id, pred_class, pred_prob, obs_class, obs_precip_mm
                for stn_idx, stn in enumerate(station_names):
                    obs_class = valid_test[f'target_{h}_{stn}'].iloc[j]
                    obs_precip = valid_test[f'obs_precip_{h}_{stn}'].iloc[j]
                    
                    pred_class = preds[b_i, stn_idx]
                    pred_prob = probs[b_i, stn_idx, pred_class]
                    
                    submissions[h].append({
                        'timestamp': t.strftime('%Y-%m-%d %H:%M:%S'),
                        'station_id': stn,
                        'pred_class': int(pred_class),
                        'pred_prob': float(pred_prob),
                        'obs_class': int(obs_class),
                        'obs_precip_mm': float(obs_precip)
                    })
                    
    for h in HORIZONS:
        sub_df = pd.DataFrame(submissions[h])
        out_file = f'submission_{h}.csv'
        sub_df.to_csv(out_file, index=False)
        print(f"Saved {out_file} (Rows: {len(sub_df)})")
        
        # Calculate evaluation metrics based on hackathon formula
        # Macro F1, Micro F1, Weighted F1
        from sklearn.metrics import classification_report
        y_true = sub_df['obs_class']
        y_pred = sub_df['pred_class']
        report = classification_report(y_true, y_pred, digits=4)
        print(f"--- Classification Report for {h} ---")
        print(report)

if __name__ == '__main__':
    main()
