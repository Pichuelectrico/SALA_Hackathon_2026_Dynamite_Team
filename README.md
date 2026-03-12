# Spatiotemporal Rain Nowcasting for San Cristóbal Island

## Overview
This project develops a machine learning system for short‑term precipitation nowcasting
using meteorological station data from San Cristóbal Island (Galápagos).

The goal is to predict rainfall intensity at +1h, +3h, and +6h horizons using multivariate
weather time‑series data collected from four stations.

Predictions are framed as a 3‑class classification problem:

| Class | Description |
|------|-------------|
| 0 | No rain |
| 1 | Light rain |
| 2 | Heavy rain |

The system uses temporal feature engineering and tabular machine learning models to produce
operational predictions suitable for early‑warning systems.

---

# Dataset

Meteorological observations collected from 4 weather stations on San Cristóbal Island.

Period: June 2015 – March 2026  
Resolution: 15‑minute observations  
Dataset size: ~1.5 million rows

Variables include:

- Air temperature
- Relative humidity
- Wind speed
- Wind direction
- Solar radiation
- Soil moisture
- Precipitation

---

# Feature Engineering

We construct spatiotemporal predictors capturing short‑term rainfall dynamics.

## Temporal Features

- hour
- day of week
- month
- hour_sin
- hour_cos

## Rainfall Lag Features

- Rain_mm_Tot_lag_1
- Rain_mm_Tot_lag_2
- Rain_mm_Tot_lag_3
- Rain_mm_Tot_lag_6
- Rain_mm_Tot_lag_12

## Rolling Statistics

- Rain_mm_Tot_rollmean_3
- Rain_mm_Tot_rollstd_3
- Rain_mm_Tot_rollmean_6
- Rain_mm_Tot_rollstd_6
- Rain_mm_Tot_rollmean_12
- Rain_mm_Tot_rollstd_12

## Cross‑Station Context

Aggregated precipitation statistics across stations:

- rain_allstations_mean_t
- rain_allstations_max_t
- rain_allstations_min_t
- rain_allstations_std_t
- rain_allstations_sum_t
- rain_otherstations_mean_t

These features help capture spatial propagation of rainfall systems across the island.

---

# Target Construction

Rainfall is accumulated over forecasting horizons.

| Horizon | Target |
|------|------|
| +1h | obs_class_1h |
| +3h | obs_class_3h |
| +6h | obs_class_6h |

Each horizon predicts accumulated precipitation intensity.

---

# Train / Validation Strategy

Temporal split:

Train: 2015 → last year  
Test: final 365 days

This prevents temporal leakage and simulates operational forecasting.

---

# Models

Two baseline models were trained:

## Logistic Regression

- strong linear baseline
- fast training
- interpretable

## Random Forest

- captures nonlinear interactions
- robust to noisy predictors
- performs well with tabular weather data

Models are trained with class‑balanced weights to mitigate class imbalance.

---

# Handling Class Imbalance

Rainfall classes are highly imbalanced:

| Class | Approx Frequency |
|------|------------------|
| No rain | ~75% |
| Light rain | ~13% |
| Heavy rain | ~10% |

To address this we use:

- class‑balanced training
- Macro‑F1 evaluation

Macro‑F1 treats each class equally.

---

# Evaluation Metrics

Primary metric:

Macro‑F1 Score

Additional metrics used internally:

- Accuracy
- Weighted F1
- Confusion matrix

---

# Bootstrap Confidence Intervals

To estimate uncertainty we apply bootstrap resampling.

Procedure:

1. Sample predictions with replacement
2. Recompute Macro‑F1
3. Repeat 1000 times
4. Compute the 95% confidence interval

---

# Final Model Performance

Macro‑F1 with Bootstrap 95% CI

| Horizon | Macro‑F1 | 95% CI |
|-------|--------|--------|
| +1h | 0.511 | [0.507 – 0.515] |
| +3h | 0.510 | [0.507 – 0.513] |
| +6h | 0.517 | [0.514 – 0.520] |

Bootstrap parameters:

B = 1000  
Test samples = 140,068

---

# Repository Structure

project/

preprocessing.py  
train_multiclass_1h.py  
train_multiclass_3h.py  
train_multiclass_6h.py  
bootstrap_macro_f1_all.py  

submission_1h.csv  
submission_3h.csv  
submission_6h.csv  

results_1h_baselines.csv  
results_3h_baselines.csv  
metrics_6h.csv  

pipeline.py  
requirements.txt  
README.md  

---

# Running the Pipeline

Install dependencies

pip install -r requirements.txt

Run preprocessing

python preprocessing.py

Train models

python train_multiclass_1h.py  
python train_multiclass_3h.py  
python train_multiclass_6h.py  

Compute bootstrap confidence intervals

python bootstrap_macro_f1_all.py

---

# Submission Files

Each prediction file contains:

| Column | Description |
|------|-------------|
| timestamp | observation time |
| station_id | station |
| pred_class | predicted class |
| pred_prob | probability of predicted class |
| obs_class | true class |
| obs_precip_mm | observed precipitation |

Files contain predictions for the final year of the dataset.

---

# Operational Prototype

Predictions can be integrated into a real‑time early warning dashboard that:

- visualizes rainfall risk per station
- displays predicted intensity levels
- shows confidence intervals
- generates early alerts

Applications include:

- conservation monitoring
- logistics planning
- flash flood alerts
- community weather awareness

---

# Future Work

Possible improvements:

- LSTM / GRU sequence models
- spatial graph neural networks
- satellite precipitation integration
- operational deployment within the USFQ weather system

---

# Authors

Hackathon SALA Team  
USFQ Rain Nowcasting Project
[README_rain_nowcasting.md](https://github.com/user-attachments/files/25924936/README_rain_nowcasting.md)
