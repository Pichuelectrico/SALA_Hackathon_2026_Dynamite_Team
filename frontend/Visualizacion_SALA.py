import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# =========================
# 1 Cargar dataset
# =========================

import os

# Default to 1h submission, but could be modified to load others
submission_file = "../submission_1h.csv"
if not os.path.exists(submission_file):
    print(f"File {submission_file} not found. Ensure pipeline.py has finished running.")
    exit(0)

df = pd.read_csv(submission_file)
df["timestamp"] = pd.to_datetime(df["timestamp"])

print("Shape:", df.shape)

# =========================
# 2 Serie temporal de predicciones vs observaciones
# =========================

station = "jun"

df_station = df[df["station_id"] == station].copy()
df_station = df_station.sort_values(by="timestamp")

sample = df_station.tail(100) # last 100 predictions

plt.figure(figsize=(12,5))
plt.plot(sample["timestamp"], sample["obs_class"], label="Observado (Métrica: Clase)", marker="o")
plt.plot(sample["timestamp"], sample["pred_class"], label="Predicho (Métrica: Clase)", marker="x", linestyle="--")
plt.title(f"Lluvia (Clases) en el tiempo - estación {station}")
plt.xlabel("Tiempo")
plt.ylabel("Clase de Lluvia (0, 1, 2)")
plt.yticks([0, 1, 2])
plt.legend()
plt.xticks(rotation=45)
plt.tight_layout()

plt.savefig("rain_time_series.png")
plt.close()

# =========================
# 3 Real vs Predicho (Matriz de Confusión Visual)
# =========================

plt.figure(figsize=(6,6))
# Add some jitter to visualize overlapping points in classes
jitter_obs = sample["obs_class"] + np.random.normal(0, 0.05, size=len(sample))
jitter_pred = sample["pred_class"] + np.random.normal(0, 0.05, size=len(sample))

plt.scatter(jitter_obs, jitter_pred, s=15, alpha=0.5)

plt.xlabel("Real (Clase)")
plt.ylabel("Predicho (Clase)")
plt.xticks([0, 1, 2])
plt.yticks([0, 1, 2])

plt.title("Real vs Predicho (Jittered)")

plt.tight_layout()

plt.savefig("real_vs_pred.png")
plt.close()

# =========================
# 4 Feature Importance
# =========================

# Si el equipo guarda importancias
try:

    feat = pd.read_csv("feature_importance.csv")

    feat = feat.sort_values("importance")

    plt.figure(figsize=(8,6))

    plt.barh(feat["feature"], feat["importance"])

    plt.title("Importancia de variables")

    plt.tight_layout()

    plt.savefig("feature_importance.png")
    plt.close()

except:
    print("No hay archivo de feature importance todavía")

# =========================
# 5 Tabla de métricas (Simplificada)
# =========================

from sklearn.metrics import classification_report

report = classification_report(df["obs_class"], df["pred_class"], output_dict=True, zero_division=0)
metrics_df = pd.DataFrame(report).transpose().round(3)

fig, ax = plt.subplots(figsize=(8, 3))
ax.axis("tight")
ax.axis("off")

table = ax.table(
    cellText=metrics_df.values,
    rowLabels=metrics_df.index,
    colLabels=metrics_df.columns,
    loc="center"
)

table.scale(1,2)

plt.savefig("model_metrics.png")
plt.close()

print("Visualizaciones actualizadas y generadas con datos de R2.")