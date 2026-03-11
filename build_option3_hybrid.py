import json
from pathlib import Path

import numpy as np
import pandas as pd
from joblib import dump, load
from sklearn.metrics import average_precision_score, f1_score, mean_absolute_error, mean_squared_error, roc_auc_score


ROOT = Path("output")
FINAL_DIR = ROOT / "final"
MODELS_DIR = ROOT / "models"

BASELINE_DIR = MODELS_DIR / "option3_two_stage"
TUNED_DIR = MODELS_DIR / "option3_two_stage_tuned"
HYBRID_DIR = MODELS_DIR / "option3_hybrid"


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


def split_df(df: pd.DataFrame, split_value: str) -> pd.DataFrame:
    return df.loc[df["split"] == split_value].copy()


def eval_hybrid(clf, reg, threshold: float, occ: pd.DataFrame, int_df: pd.DataFrame, feature_cols: list[str]) -> dict:
    out = {}
    for split_name in ["train", "val", "test"]:
        occ_s = split_df(occ, split_name)
        int_s = split_df(int_df, split_name)

        X_occ = occ_s[feature_cols]
        y_evt = occ_s["target_rain_event_next_1h"].astype(int).to_numpy()
        y_rain = occ_s["target_rain_next_1h"].astype(float).to_numpy()

        p_evt = clf.predict_proba(X_occ)[:, 1]
        yhat_evt = (p_evt >= threshold).astype(int)

        reg_all = np.clip(reg.predict(X_occ), 0, None)
        pred_expected = p_evt * reg_all
        pred_gated = np.where(p_evt >= threshold, reg_all, 0.0)

        X_int = int_s[feature_cols]
        y_int = int_s["target_rain_next_1h"].astype(float).to_numpy()
        yhat_int = np.clip(reg.predict(X_int), 0, None)

        out[split_name] = {
            "classifier_roc_auc": float(roc_auc_score(y_evt, p_evt)),
            "classifier_pr_auc": float(average_precision_score(y_evt, p_evt)),
            "classifier_f1": float(f1_score(y_evt, yhat_evt)),
            "regressor_rmse_rainy_only": rmse(y_int, yhat_int),
            "regressor_mae_rainy_only": float(mean_absolute_error(y_int, yhat_int)),
            "two_stage_expected_rmse": rmse(y_rain, pred_expected),
            "two_stage_expected_mae": float(mean_absolute_error(y_rain, pred_expected)),
            "two_stage_gated_rmse": rmse(y_rain, pred_gated),
            "two_stage_gated_mae": float(mean_absolute_error(y_rain, pred_gated)),
        }

    return out


def main() -> None:
    HYBRID_DIR.mkdir(parents=True, exist_ok=True)

    occ = pd.read_csv(FINAL_DIR / "dataset_occurrence.csv")
    int_df = pd.read_csv(FINAL_DIR / "dataset_intensity.csv")
    feature_cols = [c for c in occ.columns if c not in LEAKAGE_COLS]

    tuned_metrics = json.loads((TUNED_DIR / "metrics.json").read_text())
    threshold = float(tuned_metrics["classifier"]["decision_threshold"])

    clf = load(TUNED_DIR / "classifier_pipeline.joblib")
    reg = load(BASELINE_DIR / "regressor_pipeline.joblib")

    metrics = eval_hybrid(clf, reg, threshold, occ, int_df, feature_cols)

    dump(clf, HYBRID_DIR / "classifier_pipeline.joblib")
    dump(reg, HYBRID_DIR / "regressor_pipeline.joblib")

    output = {
        "hybrid_definition": {
            "classifier_source": str(TUNED_DIR / "classifier_pipeline.joblib"),
            "regressor_source": str(BASELINE_DIR / "regressor_pipeline.joblib"),
            "decision_threshold": threshold,
        },
        "metrics": metrics,
    }

    with open(HYBRID_DIR / "metrics.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print("Saved hybrid model package to:")
    print(HYBRID_DIR)
    print("Test expected RMSE:", metrics["test"]["two_stage_expected_rmse"])
    print("Test classifier PR-AUC:", metrics["test"]["classifier_pr_auc"])


if __name__ == "__main__":
    main()
