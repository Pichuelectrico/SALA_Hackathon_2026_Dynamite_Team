import pandas as pd
from pathlib import Path

INPUT = Path("output/all_stations_features_v2.csv")
OUTDIR = Path("output/final")
OUTDIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(INPUT)
df["TIMESTAMP"] = pd.to_datetime(df["TIMESTAMP"])
df = df.sort_values("TIMESTAMP").reset_index(drop=True)

# =========================
# 1. Definir splits temporales
# =========================
n = len(df)
train_end = int(n * 0.70)
val_end = int(n * 0.85)

df["split"] = "test"
df.loc[:train_end - 1, "split"] = "train"
df.loc[train_end:val_end - 1, "split"] = "val"

# =========================
# 2. Dataset maestro
# =========================
master_path = OUTDIR / "all_stations_master.csv"
df.to_csv(master_path, index=False)

# =========================
# 3. Dataset de ocurrencia
# =========================
occurrence_cols = [
    c for c in df.columns
    if c not in ["target_heavy_next_1h"]
]
df_occ = df[occurrence_cols].copy()

occ_path = OUTDIR / "dataset_occurrence.csv"
df_occ.to_csv(occ_path, index=False)

# =========================
# 4. Dataset de intensidad condicional
# =========================
df_int = df[df["target_rain_event_next_1h"] == 1].copy()

intensity_cols = [
    c for c in df_int.columns
    if c not in ["target_heavy_next_1h"]
]
df_int = df_int[intensity_cols]

int_path = OUTDIR / "dataset_intensity.csv"
df_int.to_csv(int_path, index=False)

# =========================
# 5. Resumen técnico
# =========================
summary_lines = []
summary_lines.append(f"Master shape: {df.shape}")
summary_lines.append(f"Occurrence shape: {df_occ.shape}")
summary_lines.append(f"Intensity shape: {df_int.shape}")
summary_lines.append("")
summary_lines.append("Split distribution (master):")
summary_lines.append(str(df["split"].value_counts()))
summary_lines.append("")
summary_lines.append("Occurrence target distribution:")
summary_lines.append(str(df["target_rain_event_next_1h"].value_counts(normalize=True)))
summary_lines.append("")
summary_lines.append("Intensity target summary:")
summary_lines.append(str(df_int["target_rain_next_1h"].describe()))
summary_lines.append("")
summary_lines.append("Stations distribution (master):")
summary_lines.append(str(df["station"].value_counts()))
summary_lines.append("")
summary_lines.append("Stations distribution (intensity):")
summary_lines.append(str(df_int["station"].value_counts()))

summary_path = OUTDIR / "dataset_summary.txt"
with open(summary_path, "w", encoding="utf-8") as f:
    f.write("\n".join(summary_lines))

print("Archivos generados:")
print(master_path)
print(occ_path)
print(int_path)
print(summary_path)

print("\nShapes:")
print("Master:", df.shape)
print("Occurrence:", df_occ.shape)
print("Intensity:", df_int.shape)

print("\nSplit distribution:")
print(df["split"].value_counts())

print("\nOccurrence target distribution:")
print(df["target_rain_event_next_1h"].value_counts(normalize=True))

print("\nIntensity target summary:")
print(df_int["target_rain_next_1h"].describe())