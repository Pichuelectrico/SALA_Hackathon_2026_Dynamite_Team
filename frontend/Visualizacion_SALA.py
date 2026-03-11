import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# =========================
# 1 Cargar dataset
# =========================

df = pd.read_csv("../output/final/dataset_intensity.csv")

df["TIMESTAMP"] = pd.to_datetime(df["TIMESTAMP"])

print("Shape:", df.shape)

# =========================
# 2 Serie temporal de lluvia
# =========================

station = "CER"

df_station = df[df["station"] == station].copy()

sample = df_station.head(500)

plt.figure(figsize=(12,5))
plt.plot(sample["TIMESTAMP"], sample["Rain_mm_Tot"])
plt.title(f"Lluvia en el tiempo - estación {station}")
plt.xlabel("Tiempo")
plt.ylabel("Rain_mm_Tot")
plt.xticks(rotation=45)
plt.tight_layout()

plt.savefig("rain_time_series.png")
plt.close()

# =========================
# 3 Real vs Predicho
# =========================

# Solo se ejecuta si existen predicciones
pred_cols = [c for c in df.columns if "pred" in c]

if len(pred_cols) > 0:

    pred = pred_cols[0]

    plt.figure(figsize=(6,6))
    plt.scatter(df["target_rain_next_1h"], df[pred], s=5)

    plt.xlabel("Real")
    plt.ylabel("Predicho")

    plt.title("Real vs Predicho")

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
# 5 Tabla de métricas
# =========================

try:

    metrics = pd.read_csv("model_metrics.csv")

    fig, ax = plt.subplots()

    ax.axis("tight")
    ax.axis("off")

    table = ax.table(
        cellText=metrics.values,
        colLabels=metrics.columns,
        loc="center"
    )

    table.scale(1,2)

    plt.savefig("model_metrics.png")
    plt.close()

except:
    print("No hay métricas todavía")

print("Visualizaciones generadas.")