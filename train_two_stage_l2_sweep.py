import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import average_precision_score, f1_score, mean_absolute_error, mean_squared_error, precision_recall_curve
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


DATA_DIR = Path("output/final")
OUT_DIR = Path("output/models/option3_l2_sweep")


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
}


def split_df(df: pd.DataFrame, split_value: str) -> pd.DataFrame:
    return df.loc[df["split"] == split_value].copy()


def rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.sqrt(mean_squared_error(y_true, y_pred)))


def best_f1_threshold(y_true: np.ndarray, y_score: np.ndarray) -> tuple[float, float]:
    precision, recall, thresholds = precision_recall_curve(y_true, y_score)
    f1_vals = 2 * precision * recall / (precision + recall + 1e-12)
    if len(thresholds) == 0:
        return 0.5, float(f1_score(y_true, (y_score >= 0.5).astype(int)))
    idx = int(np.nanargmax(f1_vals[:-1]))
    return float(thresholds[idx]), float(f1_vals[idx])


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
                    ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
                ]),
                cat_cols,
            ),
        ],
        remainder="drop",
        verbose_feature_names_out=False,
    )


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    occ = pd.read_csv(DATA_DIR / "dataset_occurrence.csv")
    int_df = pd.read_csv(DATA_DIR / "dataset_intensity.csv")
    feature_cols = [c for c in occ.columns if c not in LEAKAGE_COLS]

    X_occ_train = split_df(occ, "train")[feature_cols]
    y_occ_train = split_df(occ, "train")["target_rain_event_next_1h"].astype(int)
    X_occ_val = split_df(occ, "val")[feature_cols]
    y_occ_val = split_df(occ, "val")["target_rain_event_next_1h"].astype(int)
    X_occ_test = split_df(occ, "test")[feature_cols]
    y_occ_test = split_df(occ, "test")["target_rain_event_next_1h"].astype(int)

    X_int_train = split_df(int_df, "train")[feature_cols]
    y_int_train = split_df(int_df, "train")["target_rain_next_1h"].astype(float)
    X_int_val = split_df(int_df, "val")[feature_cols]
    y_int_val = split_df(int_df, "val")["target_rain_next_1h"].astype(float)
    X_int_test = split_df(int_df, "test")[feature_cols]
    y_int_test = split_df(int_df, "test")["target_rain_next_1h"].astype(float)

    y_rain_val = split_df(occ, "val")["target_rain_next_1h"].astype(float).to_numpy()
    y_rain_test = split_df(occ, "test")["target_rain_next_1h"].astype(float).to_numpy()

    l2_values = [0.0, 0.01, 0.03, 0.05, 0.1, 0.2, 0.4]
    rows = []

    for l2 in l2_values:
        print(f"Training L2={l2}...")
        clf = Pipeline(
            [
                ("prep", build_preprocessor(X_occ_train)),
                (
                    "model",
                    HistGradientBoostingClassifier(
                        random_state=42,
                        learning_rate=0.03,
                        max_iter=1200,
                        max_leaf_nodes=31,
                        min_samples_leaf=150,
                        l2_regularization=l2,
                        early_stopping=True,
                        validation_fraction=0.1,
                        n_iter_no_change=30,
                    ),
                ),
            ]
        )
        clf.fit(X_occ_train, y_occ_train)

        reg = Pipeline(
            [
                ("prep", build_preprocessor(X_int_train)),
                (
                    "model",
                    HistGradientBoostingRegressor(
                        random_state=42,
                        learning_rate=0.03,
                        max_iter=1400,
                        max_leaf_nodes=31,
                        min_samples_leaf=150,
                        l2_regularization=l2,
                        early_stopping=True,
                        validation_fraction=0.1,
                        n_iter_no_change=30,
                    ),
                ),
            ]
        )
        reg.fit(X_int_train, y_int_train)

        val_scores = clf.predict_proba(X_occ_val)[:, 1]
        test_scores = clf.predict_proba(X_occ_test)[:, 1]
        threshold, val_f1 = best_f1_threshold(y_occ_val.to_numpy(), val_scores)
        test_f1 = float(f1_score(y_occ_test, (test_scores >= threshold).astype(int)))

        reg_val_rainy = np.clip(reg.predict(X_int_val), 0, None)
        reg_test_rainy = np.clip(reg.predict(X_int_test), 0, None)
        reg_val_all = np.clip(reg.predict(X_occ_val), 0, None)
        reg_test_all = np.clip(reg.predict(X_occ_test), 0, None)

        expected_val = val_scores * reg_val_all
        expected_test = test_scores * reg_test_all

        row = {
            "l2": l2,
            "threshold": threshold,
            "val_classifier_pr_auc": float(average_precision_score(y_occ_val, val_scores)),
            "test_classifier_pr_auc": float(average_precision_score(y_occ_test, test_scores)),
            "val_classifier_f1": float(val_f1),
            "test_classifier_f1": test_f1,
            "val_reg_rmse_rainy_only": rmse(y_int_val.to_numpy(), reg_val_rainy),
            "test_reg_rmse_rainy_only": rmse(y_int_test.to_numpy(), reg_test_rainy),
            "val_two_stage_expected_rmse": rmse(y_rain_val, expected_val),
            "test_two_stage_expected_rmse": rmse(y_rain_test, expected_test),
            "val_two_stage_expected_mae": float(mean_absolute_error(y_rain_val, expected_val)),
            "test_two_stage_expected_mae": float(mean_absolute_error(y_rain_test, expected_test)),
        }
        rows.append(row)

    results = pd.DataFrame(rows).sort_values("val_two_stage_expected_rmse").reset_index(drop=True)
    results.to_csv(OUT_DIR / "l2_sweep_results.csv", index=False)

    best = results.iloc[0].to_dict()
    summary = {
        "selection_metric": "val_two_stage_expected_rmse",
        "best": best,
    }
    with open(OUT_DIR / "l2_sweep_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("Saved:")
    print(OUT_DIR / "l2_sweep_results.csv")
    print(OUT_DIR / "l2_sweep_summary.json")
    print("Best row:")
    print(best)


if __name__ == "__main__":
    main()
