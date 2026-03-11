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
OUT_DIR = Path("output/models/option3_two_stage")


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


def rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.sqrt(mean_squared_error(y_true, y_pred)))


def best_f1_threshold(y_true: np.ndarray, y_score: np.ndarray) -> tuple[float, float]:
    precision, recall, thresholds = precision_recall_curve(y_true, y_score)
    f1_vals = 2 * precision * recall / (precision + recall + 1e-12)

    if len(thresholds) == 0:
        return 0.5, float(f1_score(y_true, (y_score >= 0.5).astype(int)))

    best_idx = int(np.nanargmax(f1_vals[:-1]))
    threshold = float(thresholds[best_idx])
    best_f1 = float(f1_vals[best_idx])
    return threshold, best_f1


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


def make_feature_cols(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if c not in LEAKAGE_COLS]


def split_df(df: pd.DataFrame, split_value: str) -> pd.DataFrame:
    return df.loc[df["split"] == split_value].copy()


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    occ_path = DATA_DIR / "dataset_occurrence.csv"
    int_path = DATA_DIR / "dataset_intensity.csv"

    print(f"Reading occurrence dataset from {occ_path}")
    df_occ = pd.read_csv(occ_path)
    print(f"Reading intensity dataset from {int_path}")
    df_int = pd.read_csv(int_path)

    feature_cols = make_feature_cols(df_occ)
    missing_cols = [c for c in feature_cols if c not in df_int.columns]
    if missing_cols:
        raise ValueError(f"Feature columns missing in intensity dataset: {missing_cols}")

    # Stage 1: event occurrence classifier
    y_occ = df_occ["target_rain_event_next_1h"].astype(int)
    X_occ = df_occ[feature_cols]

    X_occ_train = split_df(df_occ, "train")[feature_cols]
    y_occ_train = split_df(df_occ, "train")["target_rain_event_next_1h"].astype(int)
    X_occ_val = split_df(df_occ, "val")[feature_cols]
    y_occ_val = split_df(df_occ, "val")["target_rain_event_next_1h"].astype(int)
    X_occ_test = split_df(df_occ, "test")[feature_cols]
    y_occ_test = split_df(df_occ, "test")["target_rain_event_next_1h"].astype(int)

    pre_cls = build_preprocessor(X_occ_train)
    cls = HistGradientBoostingClassifier(
        max_iter=250,
        learning_rate=0.08,
        max_leaf_nodes=63,
        random_state=42,
    )
    clf_pipeline = Pipeline([
        ("prep", pre_cls),
        ("model", cls),
    ])

    print("Training stage-1 classifier...")
    clf_pipeline.fit(X_occ_train, y_occ_train)

    val_scores = clf_pipeline.predict_proba(X_occ_val)[:, 1]
    test_scores = clf_pipeline.predict_proba(X_occ_test)[:, 1]
    threshold, best_val_f1 = best_f1_threshold(y_occ_val.to_numpy(), val_scores)
    test_pred_cls = (test_scores >= threshold).astype(int)

    cls_metrics = {
        "val_roc_auc": float(roc_auc_score(y_occ_val, val_scores)),
        "val_pr_auc": float(average_precision_score(y_occ_val, val_scores)),
        "val_best_f1": float(best_val_f1),
        "decision_threshold": float(threshold),
        "test_roc_auc": float(roc_auc_score(y_occ_test, test_scores)),
        "test_pr_auc": float(average_precision_score(y_occ_test, test_scores)),
        "test_f1": float(f1_score(y_occ_test, test_pred_cls)),
    }

    # Stage 2: intensity regressor (trained on rainy events only)
    X_int_train = split_df(df_int, "train")[feature_cols]
    y_int_train = split_df(df_int, "train")["target_rain_next_1h"].astype(float)
    X_int_val = split_df(df_int, "val")[feature_cols]
    y_int_val = split_df(df_int, "val")["target_rain_next_1h"].astype(float)
    X_int_test = split_df(df_int, "test")[feature_cols]
    y_int_test = split_df(df_int, "test")["target_rain_next_1h"].astype(float)

    pre_reg = build_preprocessor(X_int_train)
    reg = HistGradientBoostingRegressor(
        max_iter=300,
        learning_rate=0.06,
        max_leaf_nodes=63,
        random_state=42,
    )
    reg_pipeline = Pipeline([
        ("prep", pre_reg),
        ("model", reg),
    ])

    print("Training stage-2 regressor...")
    reg_pipeline.fit(X_int_train, y_int_train)

    reg_val_pred = np.clip(reg_pipeline.predict(X_int_val), 0, None)
    reg_test_pred = np.clip(reg_pipeline.predict(X_int_test), 0, None)

    reg_metrics = {
        "val_mae": float(mean_absolute_error(y_int_val, reg_val_pred)),
        "val_rmse": rmse(y_int_val.to_numpy(), reg_val_pred),
        "test_mae": float(mean_absolute_error(y_int_test, reg_test_pred)),
        "test_rmse": rmse(y_int_test.to_numpy(), reg_test_pred),
    }

    # Combined two-stage metrics on full occurrence dataset
    y_rain_val = split_df(df_occ, "val")["target_rain_next_1h"].astype(float).to_numpy()
    y_rain_test = split_df(df_occ, "test")["target_rain_next_1h"].astype(float).to_numpy()

    reg_val_all = np.clip(reg_pipeline.predict(X_occ_val), 0, None)
    reg_test_all = np.clip(reg_pipeline.predict(X_occ_test), 0, None)

    expected_val = val_scores * reg_val_all
    expected_test = test_scores * reg_test_all

    gated_val = np.where(val_scores >= threshold, reg_val_all, 0.0)
    gated_test = np.where(test_scores >= threshold, reg_test_all, 0.0)

    two_stage_metrics = {
        "val_expected_mae": float(mean_absolute_error(y_rain_val, expected_val)),
        "val_expected_rmse": rmse(y_rain_val, expected_val),
        "test_expected_mae": float(mean_absolute_error(y_rain_test, expected_test)),
        "test_expected_rmse": rmse(y_rain_test, expected_test),
        "val_gated_mae": float(mean_absolute_error(y_rain_val, gated_val)),
        "val_gated_rmse": rmse(y_rain_val, gated_val),
        "test_gated_mae": float(mean_absolute_error(y_rain_test, gated_test)),
        "test_gated_rmse": rmse(y_rain_test, gated_test),
    }

    metrics = {
        "feature_count": len(feature_cols),
        "features": feature_cols,
        "classifier": cls_metrics,
        "regressor": reg_metrics,
        "two_stage": two_stage_metrics,
    }

    dump(clf_pipeline, OUT_DIR / "classifier_pipeline.joblib")
    dump(reg_pipeline, OUT_DIR / "regressor_pipeline.joblib")
    with open(OUT_DIR / "metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    preds_preview = pd.DataFrame(
        {
            "y_true_rain": y_rain_test,
            "p_rain_event": test_scores,
            "pred_intensity_if_rain": reg_test_all,
            "pred_expected": expected_test,
            "pred_gated": gated_test,
        }
    ).head(2000)
    preds_preview.to_csv(OUT_DIR / "test_predictions_preview.csv", index=False)

    print("Saved:")
    print(OUT_DIR / "classifier_pipeline.joblib")
    print(OUT_DIR / "regressor_pipeline.joblib")
    print(OUT_DIR / "metrics.json")
    print(OUT_DIR / "test_predictions_preview.csv")
    print("\nClassifier metrics:")
    for k, v in cls_metrics.items():
        print(f"  {k}: {v}")
    print("\nRegressor metrics:")
    for k, v in reg_metrics.items():
        print(f"  {k}: {v}")
    print("\nTwo-stage metrics:")
    for k, v in two_stage_metrics.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()