import pandas as pd
import matplotlib.pyplot as plt

# 1) Cargar dataset
df = pd.read_csv("output/final/all_stations_master.csv")

# 2) Convertir timestamp
df["TIMESTAMP"] = pd.to_datetime(df["TIMESTAMP"])

# 3) Resumen básico
print("Shape:", df.shape)
print("\nColumnas:")
print(df.columns.tolist())
print("\nPrimeras filas:")
print(df.head())

# 4) Elegir una estación para visualizar
station_name = "CER"
df_station = df[df["station"] == station_name].copy()

print(f"\nFilas de {station_name}:", df_station.shape[0])

# 5) Tomar una muestra para que la gráfica sea legible
sample = df_station.head(300)

# 6) Graficar lluvia en el tiempo
plt.figure(figsize=(12, 5))
plt.plot(sample["TIMESTAMP"], sample["Rain_mm_Tot"])
plt.title(f"Lluvia en el tiempo - estación {station_name}")
plt.xlabel("Tiempo")
plt.ylabel("Rain_mm_Tot")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

# 7) Graficar lluvia actual vs target futuro
plt.figure(figsize=(8, 5))
plt.scatter(sample["Rain_mm_Tot"], sample["target_rain_next_1h"], s=10)
plt.title(f"Lluvia actual vs lluvia futura - {station_name}")
plt.xlabel("Rain_mm_Tot en t")
plt.ylabel("target_rain_next_1h")
plt.tight_layout()
plt.savefig('plot.png', dpi=150, bbox_inches='tight')

