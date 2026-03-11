import json
from pathlib import Path

import numpy as np
import pandas as pd
from joblib import dump
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    average_precision_score,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_recall_curve,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


DATA_DIR = Path("output/final")
OUT_DIR = Path("output/models/option4_station_specific")


LEAKAGE_COLS = {
    "TIMESTAMP",
    "split",
    "target_rain_event_next_1h",
    "target_rain_next_1h",
    "target_heavy_next_1h",
    "target_heavy_rain_t1",
    "target_rain_t1",
    "Rain_mm_Tot_lead_1",
    "Rain_mm_Tot_lead_2",
    "Rain_mm_Tot_lead_3",
    "Rain_mm_Tot_lead_4",
    "station",
}


def rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.sqrt(mean_squared_error(y_true, y_pred)))


def best_f1_threshold(y_true: np.ndarray, y_score: np.ndarray) -> tuple[float, float]:
    precision, recall, thresholds = precision_recall_curve(y_true, y_score)
    f1_vals = 2 * precision * recall / (precision + recall + 1e-12)

    if len(thresholds) == 0:
        return 0.5, float(f1_score(y_true, (y_score >= 0.5).astype(int)))

    best_idx = int(np.nanargmax(f1_vals[:-1]))
    return float(thresholds[best_idx]), float(f1_vals[best_idx])


def build_preprocessor(feature_df: pd.DataFrame) -> ColumnTransformer:
    cat_cols = [c for c in feature_df.columns if feature_df[c].dtype == "object"]
    num_cols = [c for c in feature_df.columns if c not in cat_cols]
    return ColumnTransformer(
        transformers=[
            (
                "num",
                Pipeline([
                    ("imputer", SimpleImputer(strategy="median")),
                ]),
                num_cols,
            ),
            (
                "cat",
                Pipeline([
                    ("imputer", SimpleImputer(strategy="most_frequent")),
                    (
                        "onehot",
                        OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                    ),
                ]),
                cat_cols,
            ),
        ],
        remainder="drop",
        verbose_feature_names_out=False,
    )


def split_df(df: pd.DataFrame, split_value: str) -> pd.DataFrame:
    return df.loc[df["split"] == split_value].copy()


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    df_occ = pd.read_csv(DATA_DIR / "dataset_occurrence.csv")
    df_int = pd.read_csv(DATA_DIR / "dataset_intensity.csv")

    feature_cols = [c for c in df_occ.columns if c not in LEAKAGE_COLS]

    station_metrics = []
    stations = sorted(df_occ["station"].dropna().unique().tolist())

    for station in stations:
        print(f"\\n=== Training station {station} ===")
        out_station = OUT_DIR / station
        out_station.mkdir(parents=True, exist_ok=True)

        occ_s = df_occ[df_occ["station"] == station].copy()
        int_s = df_int[df_int["station"] == station].copy()

        # Safety checks for tiny splits
        occ_train = split_df(occ_s, "train")
        occ_val = split_df(occ_s, "val")
        occ_test = split_df(occ_s, "test")
        int_train = split_df(int_s, "train")
        int_val = split_df(int_s, "val")
        int_test = split_df(int_s, "test")

        if occ_train["target_rain_event_next_1h"].nunique() < 2:
            print(f"Skipping station {station}: classifier train split has one class")
            continue
        if len(int_train) < 200:
            print(f"Skipping station {station}: too few rainy samples for regression")
            continue

        X_occ_train = occ_train[feature_cols]
        y_occ_train = occ_train["target_rain_event_next_1h"].astype(int)
        X_occ_val = occ_val[feature_cols]
        y_occ_val = occ_val["target_rain_event_next_1h"].astype(int)
        X_occ_test = occ_test[feature_cols]
        y_occ_test = occ_test["target_rain_event_next_1h"].astype(int)

        clf = Pipeline(
            [
                ("prep", build_preprocessor(X_occ_train)),
                (
                    "model",
                    HistGradientBoostingClassifier(
                        max_iter=250,
                        learning_rate=0.08,
                        max_leaf_nodes=63,
                        random_state=42,
                    ),
                ),
            ]
        )
        clf.fit(X_occ_train, y_occ_train)

        val_scores = clf.predict_proba(X_occ_val)[:, 1]
        test_scores = clf.predict_proba(X_occ_test)[:, 1]
        threshold, val_best_f1 = best_f1_threshold(y_occ_val.to_numpy(), val_scores)
        test_pred = (test_scores >= threshold).astype(int)

        X_int_train = int_train[feature_cols]
        y_int_train = int_train["target_rain_next_1h"].astype(float)
        X_int_val = int_val[feature_cols]
        y_int_val = int_val["target_rain_next_1h"].astype(float)
        X_int_test = int_test[feature_cols]
        y_int_test = int_test["target_rain_next_1h"].astype(float)

        reg = Pipeline(
            [
                ("prep", build_preprocessor(X_int_train)),
                (
                    "model",
                    HistGradientBoostingRegressor(
                        max_iter=300,
                        learning_rate=0.06,
                        max_leaf_nodes=63,
                        random_state=42,
                    ),
                ),
            ]
        )
        reg.fit(X_int_train, y_int_train)

        reg_val_pred = np.clip(reg.predict(X_int_val), 0, None)
        reg_test_pred = np.clip(reg.predict(X_int_test), 0, None)

        y_rain_val = occ_val["target_rain_next_1h"].astype(float).to_numpy()
        y_rain_test = occ_test["target_rain_next_1h"].astype(float).to_numpy()
        reg_val_all = np.clip(reg.predict(X_occ_val), 0, None)
        reg_test_all = np.clip(reg.predict(X_occ_test), 0, None)

        expected_val = val_scores * reg_val_all
        expected_test = test_scores * reg_test_all
        gated_val = np.where(val_scores >= threshold, reg_val_all, 0.0)
        gated_test = np.where(test_scores >= threshold, reg_test_all, 0.0)

        metrics = {
            "station": station,
            "n_occ_train": int(len(occ_train)),
            "n_occ_val": int(len(occ_val)),
            "n_occ_test": int(len(occ_test)),
            "n_int_train": int(len(int_train)),
            "n_int_val": int(len(int_val)),
            "n_int_test": int(len(int_test)),
            "classifier_val_roc_auc": float(roc_auc_score(y_occ_val, val_scores)),
            "classifier_val_pr_auc": float(average_precision_score(y_occ_val, val_scores)),
            "classifier_val_best_f1": float(val_best_f1),
            "classifier_threshold": float(threshold),
            "classifier_test_roc_auc": float(roc_auc_score(y_occ_test, test_scores)),
            "classifier_test_pr_auc": float(average_precision_score(y_occ_test, test_scores)),
            "classifier_test_f1": float(f1_score(y_occ_test, test_pred)),
            "regressor_val_mae": float(mean_absolute_error(y_int_val, reg_val_pred)),
            "regressor_val_rmse": rmse(y_int_val.to_numpy(), reg_val_pred),
            "regressor_test_mae": float(mean_absolute_error(y_int_test, reg_test_pred)),
            "regressor_test_rmse": rmse(y_int_test.to_numpy(), reg_test_pred),
            "two_stage_val_expected_mae": float(mean_absolute_error(y_rain_val, expected_val)),
            "two_stage_val_expected_rmse": rmse(y_rain_val, expected_val),
            "two_stage_test_expected_mae": float(mean_absolute_error(y_rain_test, expected_test)),
            "two_stage_test_expected_rmse": rmse(y_rain_test, expected_test),
            "two_stage_val_gated_mae": float(mean_absolute_error(y_rain_val, gated_val)),
            "two_stage_val_gated_rmse": rmse(y_rain_val, gated_val),
            "two_stage_test_gated_mae": float(mean_absolute_error(y_rain_test, gated_test)),
            "two_stage_test_gated_rmse": rmse(y_rain_test, gated_test),
        }

        dump(clf, out_station / "classifier_pipeline.joblib")
        dump(reg, out_station / "regressor_pipeline.joblib")
        with open(out_station / "metrics.json", "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2)

        station_metrics.append(metrics)

    if not station_metrics:
        raise RuntimeError("No station models were trained. Check class balance and sample sizes.")

    metrics_df = pd.DataFrame(station_metrics)
    metrics_df.to_csv(OUT_DIR / "station_metrics_summary.csv", index=False)

    aggregate = {
        "n_stations": int(len(metrics_df)),
        "mean_two_stage_test_expected_rmse": float(metrics_df["two_stage_test_expected_rmse"].mean()),
        "mean_two_stage_test_gated_rmse": float(metrics_df["two_stage_test_gated_rmse"].mean()),
        "mean_classifier_test_pr_auc": float(metrics_df["classifier_test_pr_auc"].mean()),
        "mean_classifier_test_f1": float(metrics_df["classifier_test_f1"].mean()),
    }

    with open(OUT_DIR / "aggregate_metrics.json", "w", encoding="utf-8") as f:
        json.dump(aggregate, f, indent=2)

    print("\\nSaved station-specific outputs to:")
    print(OUT_DIR)
    print("- station_metrics_summary.csv")
    print("- aggregate_metrics.json")
    print("- <station>/classifier_pipeline.joblib")
    print("- <station>/regressor_pipeline.joblib")
    print("- <station>/metrics.json")


if __name__ == "__main__":
    main()