import pandas as pd
import numpy as np
from pathlib import Path

INPUT = Path(r"C:\\Users\\AGES\\Documents\\SALA\\Hackaton_Sala\\output\\final\\all_stations_master.csv")
OUTDIR = Path(r"C:\\Users\\AGES\\Documents\\SALA\\Hackaton_Sala\\output\\official")
OUTDIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(INPUT)
df["TIMESTAMP"] = pd.to_datetime(df["TIMESTAMP"])
df = df.sort_values(["station", "TIMESTAMP"]).reset_index(drop=True)

rain_col = "Rain_mm_Tot"

# =========================
# 1. Metadata temporal útil
# =========================
df["year"] = df["TIMESTAMP"].dt.year

max_time = df["TIMESTAMP"].max()
last_year_start = max_time - pd.DateOffset(years=1)
df["is_last_year"] = (df["TIMESTAMP"] >= last_year_start).astype(int)

# =========================
# 2. Construir acumulados futuros oficiales
# =========================
for k in range(1, 25):
    df[f"{rain_col}_lead_{k}"] = df.groupby("station")[rain_col].shift(-k)

# +1h = 4 pasos
df["obs_precip_1h"] = sum(df[f"{rain_col}_lead_{k}"] for k in range(1, 5))

# +3h = 12 pasos
df["obs_precip_3h"] = sum(df[f"{rain_col}_lead_{k}"] for k in range(1, 13))

# +6h = 24 pasos
df["obs_precip_6h"] = sum(df[f"{rain_col}_lead_{k}"] for k in range(1, 25))

# =========================
# 3. Clases oficiales
# =========================
def classify_precip(y, light_threshold):
    if pd.isna(y):
        return np.nan
    if y == 0:
        return 0
    elif y <= light_threshold:
        return 1
    else:
        return 2

df["obs_class_1h"] = df["obs_precip_1h"].apply(lambda y: classify_precip(y, 0.254))
df["obs_class_3h"] = df["obs_precip_3h"].apply(lambda y: classify_precip(y, 0.508))
df["obs_class_6h"] = df["obs_precip_6h"].apply(lambda y: classify_precip(y, 0.762))

# =========================
# 4. Quitar filas sin horizonte completo
# =========================
required_targets = [
    "obs_precip_1h", "obs_class_1h",
    "obs_precip_3h", "obs_class_3h",
    "obs_precip_6h", "obs_class_6h"
]
df_final = df.dropna(subset=required_targets).reset_index(drop=True)

df_final["obs_class_1h"] = df_final["obs_class_1h"].astype(int)
df_final["obs_class_3h"] = df_final["obs_class_3h"].astype(int)
df_final["obs_class_6h"] = df_final["obs_class_6h"].astype(int)

# =========================
# 5. Eliminar columnas lead_* para evitar leakage
# =========================
lead_cols = [c for c in df_final.columns if c.startswith(f"{rain_col}_lead_")]
df_final = df_final.drop(columns=lead_cols)

# =========================
# 6. Guardar master oficial
# =========================
master_path = OUTDIR / "official_master_multihorizon.csv"
df_final.to_csv(master_path, index=False)

# =========================
# 7. Guardar datasets por horizonte
# =========================
common_drop = [
    "obs_precip_1h", "obs_class_1h",
    "obs_precip_3h", "obs_class_3h",
    "obs_precip_6h", "obs_class_6h",
]

# 1h
keep_1h = [c for c in df_final.columns if c not in ["obs_precip_3h", "obs_class_3h", "obs_precip_6h", "obs_class_6h"]]
df_1h = df_final[keep_1h].copy()
df_1h.to_csv(OUTDIR / "dataset_1h.csv", index=False)

# 3h
keep_3h = [c for c in df_final.columns if c not in ["obs_precip_1h", "obs_class_1h", "obs_precip_6h", "obs_class_6h"]]
df_3h = df_final[keep_3h].copy()
df_3h.to_csv(OUTDIR / "dataset_3h.csv", index=False)

# 6h
keep_6h = [c for c in df_final.columns if c not in ["obs_precip_1h", "obs_class_1h", "obs_precip_3h", "obs_class_3h"]]
df_6h = df_final[keep_6h].copy()
df_6h.to_csv(OUTDIR / "dataset_6h.csv", index=False)

# =========================
# 8. Resumen
# =========================
summary_lines = []
summary_lines.append(f"Official master shape: {df_final.shape}")
summary_lines.append(f"Dataset 1h shape: {df_1h.shape}")
summary_lines.append(f"Dataset 3h shape: {df_3h.shape}")
summary_lines.append(f"Dataset 6h shape: {df_6h.shape}")
summary_lines.append("")

summary_lines.append("Class distribution 1h:")
summary_lines.append(str(df_final["obs_class_1h"].value_counts(normalize=True).sort_index()))
summary_lines.append("")

summary_lines.append("Class distribution 3h:")
summary_lines.append(str(df_final["obs_class_3h"].value_counts(normalize=True).sort_index()))
summary_lines.append("")

summary_lines.append("Class distribution 6h:")
summary_lines.append(str(df_final["obs_class_6h"].value_counts(normalize=True).sort_index()))
summary_lines.append("")

summary_lines.append("Stations:")
summary_lines.append(str(df_final["station"].value_counts()))
summary_lines.append("")

summary_lines.append("Last year flag:")
summary_lines.append(str(df_final["is_last_year"].value_counts()))

summary_path = OUTDIR / "official_summary.txt"
with open(summary_path, "w", encoding="utf-8") as f:
    f.write("\n".join(summary_lines))

print("Archivos generados:")
print(master_path)
print(OUTDIR / "dataset_1h.csv")
print(OUTDIR / "dataset_3h.csv")
print(OUTDIR / "dataset_6h.csv")
print(summary_path)

print("\nShape final master:")
print(df_final.shape)

print("\nShape dataset 1h:")
print(df_1h.shape)

print("\nShape dataset 3h:")
print(df_3h.shape)

print("\nShape dataset 6h:")
print(df_6h.shape)

print("\nDistribución de clases +1h:")
print(df_final["obs_class_1h"].value_counts(normalize=True).sort_index())

print("\nDistribución de clases +3h:")
print(df_final["obs_class_3h"].value_counts(normalize=True).sort_index())

print("\nDistribución de clases +6h:")
print(df_final["obs_class_6h"].value_counts(normalize=True).sort_index())

print("\nÚltimo año:")
print(df_final["is_last_year"].value_counts())

print("\nPreview:")
print(df_final[[
    "TIMESTAMP", "station",
    "obs_precip_1h", "obs_class_1h",
    "obs_precip_3h", "obs_class_3h",
    "obs_precip_6h", "obs_class_6h",
    "is_last_year"
]].head())