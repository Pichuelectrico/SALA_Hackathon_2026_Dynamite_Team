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
OUT_DIR = Path("output/models/option3_two_stage_tuned")


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
                    ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
                ]),
                cat_cols,
            ),
        ],
        remainder="drop",
        verbose_feature_names_out=False,
    )


def split_df(df: pd.DataFrame, split_value: str) -> pd.DataFrame:
    return df.loc[df["split"] == split_value].copy()


def select_classifier(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_val: pd.DataFrame,
    y_val: pd.Series,
) -> tuple[Pipeline, dict, float, float]:
    # HistGradientBoosting supports L2 regularization + early stopping.
    # It does not support explicit L1, so we prioritize robust L2 + conservative complexity.
    grid = [
        {
            "learning_rate": 0.03,
            "max_iter": 1200,
            "max_leaf_nodes": 31,
            "min_samples_leaf": 100,
            "l2_regularization": 0.05,
        },
        {
            "learning_rate": 0.03,
            "max_iter": 1200,
            "max_leaf_nodes": 31,
            "min_samples_leaf": 150,
            "l2_regularization": 0.1,
        },
        {
            "learning_rate": 0.05,
            "max_iter": 900,
            "max_leaf_nodes": 31,
            "min_samples_leaf": 100,
            "l2_regularization": 0.2,
        },
    ]

    best_score = -np.inf
    best_pipeline = None
    best_params = None
    best_threshold = 0.5
    best_val_f1 = 0.0

    for params in grid:
        model = HistGradientBoostingClassifier(
            random_state=42,
            early_stopping=True,
            validation_fraction=0.1,
            n_iter_no_change=30,
            **params,
        )
        pipe = Pipeline([
            ("prep", build_preprocessor(X_train)),
            ("model", model),
        ])
        pipe.fit(X_train, y_train)

        val_scores = pipe.predict_proba(X_val)[:, 1]
        val_pr_auc = float(average_precision_score(y_val, val_scores))
        threshold, val_f1 = best_f1_threshold(y_val.to_numpy(), val_scores)

        if val_pr_auc > best_score:
            best_score = val_pr_auc
            best_pipeline = pipe
            best_params = params
            best_threshold = threshold
            best_val_f1 = val_f1

    return best_pipeline, best_params, float(best_threshold), float(best_val_f1)


def select_regressor(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_val: pd.DataFrame,
    y_val: pd.Series,
) -> tuple[Pipeline, dict, float]:
    grid = [
        {
            "learning_rate": 0.03,
            "max_iter": 1400,
            "max_leaf_nodes": 31,
            "min_samples_leaf": 100,
            "l2_regularization": 0.05,
        },
        {
            "learning_rate": 0.03,
            "max_iter": 1400,
            "max_leaf_nodes": 31,
            "min_samples_leaf": 150,
            "l2_regularization": 0.1,
        },
        {
            "learning_rate": 0.05,
            "max_iter": 1000,
            "max_leaf_nodes": 31,
            "min_samples_leaf": 120,
            "l2_regularization": 0.2,
        },
    ]

    best_rmse = np.inf
    best_pipeline = None
    best_params = None

    for params in grid:
        model = HistGradientBoostingRegressor(
            random_state=42,
            early_stopping=True,
            validation_fraction=0.1,
            n_iter_no_change=30,
            **params,
        )
        pipe = Pipeline([
            ("prep", build_preprocessor(X_train)),
            ("model", model),
        ])
        pipe.fit(X_train, y_train)

        val_pred = np.clip(pipe.predict(X_val), 0, None)
        val_rmse = rmse(y_val.to_numpy(), val_pred)
        if val_rmse < best_rmse:
            best_rmse = val_rmse
            best_pipeline = pipe
            best_params = params

    return best_pipeline, best_params, float(best_rmse)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    df_occ = pd.read_csv(DATA_DIR / "dataset_occurrence.csv")
    df_int = pd.read_csv(DATA_DIR / "dataset_intensity.csv")

    feature_cols = [c for c in df_occ.columns if c not in LEAKAGE_COLS]

    X_occ_train = split_df(df_occ, "train")[feature_cols]
    y_occ_train = split_df(df_occ, "train")["target_rain_event_next_1h"].astype(int)
    X_occ_val = split_df(df_occ, "val")[feature_cols]
    y_occ_val = split_df(df_occ, "val")["target_rain_event_next_1h"].astype(int)
    X_occ_test = split_df(df_occ, "test")[feature_cols]
    y_occ_test = split_df(df_occ, "test")["target_rain_event_next_1h"].astype(int)

    print("Selecting classifier with early stopping + L2 regularization...")
    clf, clf_params, threshold, val_best_f1 = select_classifier(
        X_occ_train,
        y_occ_train,
        X_occ_val,
        y_occ_val,
    )

    val_scores = clf.predict_proba(X_occ_val)[:, 1]
    test_scores = clf.predict_proba(X_occ_test)[:, 1]
    test_pred_cls = (test_scores >= threshold).astype(int)

    cls_metrics = {
        "val_roc_auc": float(roc_auc_score(y_occ_val, val_scores)),
        "val_pr_auc": float(average_precision_score(y_occ_val, val_scores)),
        "val_best_f1": float(val_best_f1),
        "decision_threshold": float(threshold),
        "test_roc_auc": float(roc_auc_score(y_occ_test, test_scores)),
        "test_pr_auc": float(average_precision_score(y_occ_test, test_scores)),
        "test_f1": float(f1_score(y_occ_test, test_pred_cls)),
    }

    X_int_train = split_df(df_int, "train")[feature_cols]
    y_int_train = split_df(df_int, "train")["target_rain_next_1h"].astype(float)
    X_int_val = split_df(df_int, "val")[feature_cols]
    y_int_val = split_df(df_int, "val")["target_rain_next_1h"].astype(float)
    X_int_test = split_df(df_int, "test")[feature_cols]
    y_int_test = split_df(df_int, "test")["target_rain_next_1h"].astype(float)

    print("Selecting regressor with early stopping + L2 regularization...")
    reg, reg_params, best_val_rmse = select_regressor(
        X_int_train,
        y_int_train,
        X_int_val,
        y_int_val,
    )

    reg_val_pred = np.clip(reg.predict(X_int_val), 0, None)
    reg_test_pred = np.clip(reg.predict(X_int_test), 0, None)

    reg_metrics = {
        "best_val_rmse_from_search": float(best_val_rmse),
        "val_mae": float(mean_absolute_error(y_int_val, reg_val_pred)),
        "val_rmse": rmse(y_int_val.to_numpy(), reg_val_pred),
        "test_mae": float(mean_absolute_error(y_int_test, reg_test_pred)),
        "test_rmse": rmse(y_int_test.to_numpy(), reg_test_pred),
    }

    y_rain_val = split_df(df_occ, "val")["target_rain_next_1h"].astype(float).to_numpy()
    y_rain_test = split_df(df_occ, "test")["target_rain_next_1h"].astype(float).to_numpy()
    reg_val_all = np.clip(reg.predict(X_occ_val), 0, None)
    reg_test_all = np.clip(reg.predict(X_occ_test), 0, None)

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

    metadata = {
        "regularization_note": "Using HistGradientBoosting with L2 regularization and early stopping. Explicit L1 is not available in this sklearn model family.",
        "selected_classifier_params": clf_params,
        "selected_regressor_params": reg_params,
        "feature_count": len(feature_cols),
        "features": feature_cols,
    }

    metrics = {
        "metadata": metadata,
        "classifier": cls_metrics,
        "regressor": reg_metrics,
        "two_stage": two_stage_metrics,
    }

    dump(clf, OUT_DIR / "classifier_pipeline.joblib")
    dump(reg, OUT_DIR / "regressor_pipeline.joblib")
    with open(OUT_DIR / "metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    preview = pd.DataFrame(
        {
            "y_true_rain": y_rain_test,
            "p_rain_event": test_scores,
            "pred_intensity_if_rain": reg_test_all,
            "pred_expected": expected_test,
            "pred_gated": gated_test,
        }
    ).head(2000)
    preview.to_csv(OUT_DIR / "test_predictions_preview.csv", index=False)

    print("Saved tuned artifacts to:")
    print(OUT_DIR)
    print("Classifier params:", clf_params)
    print("Regressor params:", reg_params)
    print("Two-stage test expected RMSE:", two_stage_metrics["test_expected_rmse"])
    print("Classifier test PR-AUC:", cls_metrics["test_pr_auc"])


if __name__ == "__main__":
    main()