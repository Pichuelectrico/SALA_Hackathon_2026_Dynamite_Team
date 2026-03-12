import pandas as pd
import numpy as np
from pathlib import Path

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, f1_score
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier

# =========================
# 1. Cargar datos
# =========================
DATA_PATH = Path(r"C:\Users\AGES\Documents\SALA\Hackaton_Sala\output\official\dataset_3h.csv")

df = pd.read_csv(DATA_PATH)
df["TIMESTAMP"] = pd.to_datetime(df["TIMESTAMP"])
df["station"] = df["station"].astype(str)
df = df.sort_values(["TIMESTAMP", "station"]).reset_index(drop=True)

print("Shape total:", df.shape)
print("Columnas:", df.columns.tolist())

# =========================
# 2. Definir target y split
# =========================
target = "obs_class_3h"

train_df = df[df["is_last_year"] == 0].copy()
test_df  = df[df["is_last_year"] == 1].copy()

print("\nTrain shape:", train_df.shape)
print("Test shape:", test_df.shape)

print("\nDistribución target train:")
print(train_df[target].value_counts(normalize=True).sort_index())

print("\nDistribución target test:")
print(test_df[target].value_counts(normalize=True).sort_index())

# =========================
# 3. Excluir targets y columnas auxiliares
# =========================
drop_cols = [
    "TIMESTAMP",
    "obs_precip_1h", "obs_class_1h",
    "obs_precip_3h", "obs_class_3h",
    "obs_precip_6h", "obs_class_6h",
    "target_rain_t1",
    "target_heavy_rain_t1",
    "target_rain_next_1h",
    "target_rain_event_next_1h",
    "target_heavy_next_1h",
    "split",
]

X_train = train_df.drop(columns=[c for c in drop_cols if c in train_df.columns])
y_train = train_df[target]

X_test = test_df.drop(columns=[c for c in drop_cols if c in test_df.columns])
y_test = test_df[target]

# =========================
# 4. Definir columnas categóricas y numéricas
# =========================
cat_cols = ["station"]
num_cols = [c for c in X_train.columns if c not in cat_cols]

print("\nColumnas categóricas:", cat_cols)
print("Número de columnas numéricas:", len(num_cols))
print("Primeras columnas numéricas:", num_cols[:10])

# =========================
# 5. Preprocesamiento
# =========================
preprocess = ColumnTransformer([
    ("num", Pipeline([
        ("imputer", SimpleImputer(strategy="median"))
    ]), num_cols),
    ("cat", Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore"))
    ]), cat_cols)
])

# =========================
# 6. Modelos
# =========================
models = {
    "logreg": LogisticRegression(
        max_iter=2000,
        class_weight="balanced"
    ),
    "rf": RandomForestClassifier(
        n_estimators=300,
        random_state=42,
        class_weight="balanced_subsample",
        n_jobs=-1
    )
}

# =========================
# 7. Entrenamiento y evaluación
# =========================
results = []

for name, model in models.items():
    print(f"\n{'='*20} {name} {'='*20}")

    pipe = Pipeline([
        ("prep", preprocess),
        ("model", model)
    ])

    pipe.fit(X_train, y_train)
    y_pred = pipe.predict(X_test)

    acc = accuracy_score(y_test, y_pred)
    f1_macro = f1_score(y_test, y_pred, average="macro")
    f1_weighted = f1_score(y_test, y_pred, average="weighted")

    print("Accuracy:", round(acc, 4))
    print("Macro F1:", round(f1_macro, 4))
    print("Weighted F1:", round(f1_weighted, 4))

    print("\nClassification report:")
    print(classification_report(y_test, y_pred, digits=4))

    print("Confusion matrix:")
    print(confusion_matrix(y_test, y_pred))

    print("\nDistribución de predicciones:")
    print(pd.Series(y_pred).value_counts(normalize=True).sort_index())

    results.append({
        "model": name,
        "accuracy": acc,
        "f1_macro": f1_macro,
        "f1_weighted": f1_weighted
    })

# =========================
# 8. Guardar resumen
# =========================
results_df = pd.DataFrame(results)
out_path = DATA_PATH.parent / "results_3h_baselines.csv"
results_df.to_csv(out_path, index=False)

print("\nResumen guardado en:", out_path)
print(results_df)

# =========================
# 9. Guardar submission oficial 3h
# =========================
best_model_name = "logreg"   # cambia a "rf" si decides usar random forest
best_model = models[best_model_name]

final_pipe = Pipeline([
    ("prep", preprocess),
    ("model", best_model)
])

final_pipe.fit(X_train, y_train)

y_pred = final_pipe.predict(X_test)
y_proba = final_pipe.predict_proba(X_test)

pred_prob = y_proba[np.arange(len(y_pred)), y_pred]

submission = pd.DataFrame({
    "timestamp": test_df["TIMESTAMP"].dt.strftime("%Y-%m-%d %H:%M:%S"),
    "station_id": test_df["station"],
    "pred_class": y_pred.astype(int),
    "pred_prob": pred_prob.astype(float),
    "obs_class": test_df["obs_class_3h"].astype(int),
    "obs_precip_mm": test_df["obs_precip_3h"].astype(float),
})

submission_path = DATA_PATH.parent / "submission_3h.csv"
submission.to_csv(submission_path, index=False)

print("\nSubmission guardado en:", submission_path)
print(submission.head())