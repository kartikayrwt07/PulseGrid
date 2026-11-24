"""
Leakage-Free Model Training, 5-Fold Stratified CV & Calibration Audit Pipeline.

Trains 3 classifiers and 1 continuous score regressor on Weeks 1..8 features
to predict Weeks 10..12 outcomes, outputting holdout + 5-fold CV + Brier score
+ 5-bin calibration reliability curve to model_audit.json.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.calibration import calibration_curve
from sklearn.ensemble import (
    GradientBoostingClassifier,
    GradientBoostingRegressor,
    RandomForestClassifier,
)
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    brier_score_loss,
    confusion_matrix,
    f1_score,
    mean_absolute_error,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.analytics.features import FEATURE_LABELS, FEATURE_NAMES, extract_features  # noqa: E402
from app.analytics.ml_inference import RISK_TIER_LABELS, reload_models  # noqa: E402
from app.core.database import SessionLocal  # noqa: E402
from app.services.snapshot_service import load_records_frame, recompute_all_snapshots  # noqa: E402

ARTIFACTS_DIR = BACKEND_DIR / "ml" / "artifacts"
CUTOFF_WEEK = 8
RANDOM_STATE = 42


def load_weekly_dataframe() -> pd.DataFrame:
    csv_path = ARTIFACTS_DIR / "cohort_training_weeks.csv"
    if csv_path.exists():
        return pd.read_csv(csv_path)
    with SessionLocal() as db:
        return load_records_frame(db)


def compute_future_targets(df: pd.DataFrame, target_start_week: int = 10) -> pd.DataFrame:
    """Build future tier (0..3) & composite strictly from Weeks >= 10."""
    fut = df[df["week"] >= target_start_week]
    subj_agg = (
        fut.groupby(["student_id", "subject_id"])[
            ["attendance_pct", "assignment_score", "internal_score"]
        ]
        .mean()
        .reset_index()
    )
    stu = (
        subj_agg.groupby("student_id")
        .agg(
            att_mean=("attendance_pct", "mean"),
            att_min=("attendance_pct", "min"),
            assign_mean=("assignment_score", "mean"),
            ia_mean=("internal_score", "mean"),
        )
        .reset_index()
    )
    stu["target_score"] = (
        0.25 * stu["att_mean"] + 0.25 * stu["assign_mean"] + 0.50 * stu["ia_mean"]
    )

    def _assign_tier(row: pd.Series) -> int:
        if (
            row["target_score"] < 53.0
            or row["att_min"] < 50.0
            or row["ia_mean"] < 41.0
            or (
                row["target_score"] < 62.0
                and row["att_mean"] < 65.0
                and row["ia_mean"] < 57.5
            )
        ):
            return 3
        if row["ia_mean"] < 50.0 or row["target_score"] < 68.0 or row["att_min"] < 62.0:
            return 2
        if row["att_min"] < 78.0 or row["target_score"] < 83.2:
            return 1
        return 0

    stu["target_tier"] = stu.apply(_assign_tier, axis=1).astype(int)
    return stu[["student_id", "target_tier", "target_score"]]


def _cross_validate_classifier(
    base_clf: Any, x_all: np.ndarray, y_tier: np.ndarray
) -> tuple[dict[str, float], np.ndarray]:
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    oof_probs = np.zeros((len(y_tier), len(RISK_TIER_LABELS)), dtype=float)
    recalls: list[float] = []
    f1s: list[float] = []
    aucs: list[float] = []

    for tr_idx, va_idx in skf.split(x_all, y_tier):
        fold_clf = clone(base_clf)
        fold_clf.fit(x_all[tr_idx], y_tier[tr_idx])
        probs = fold_clf.predict_proba(x_all[va_idx])
        oof_probs[va_idx] = probs
        preds = np.argmax(probs, axis=1)
        recalls.append(
            float(
                recall_score(
                    (y_tier[va_idx] >= 2).astype(int), (preds >= 2).astype(int), zero_division=0
                )
            )
        )
        f1s.append(float(f1_score(y_tier[va_idx], preds, average="macro", zero_division=0)))
        aucs.append(
            float(roc_auc_score(y_tier[va_idx], probs, multi_class="ovr", average="macro"))
        )

    return {
        "cv_at_risk_recall_mean": round(float(np.mean(recalls)), 4),
        "cv_at_risk_recall_std": round(float(np.std(recalls)), 4),
        "cv_macro_f1_mean": round(float(np.mean(f1s)), 4),
        "cv_macro_f1_std": round(float(np.std(f1s)), 4),
        "cv_roc_auc_mean": round(float(np.mean(aucs)), 4),
    }, oof_probs


def _calibration_stats(
    y_tier: np.ndarray, oof_probs: np.ndarray
) -> tuple[float, list[dict[str, Any]]]:
    y_bin = (y_tier >= 2).astype(int)
    p_risk = np.clip(oof_probs[:, 2] + oof_probs[:, 3], 0.0, 1.0)
    brier = round(float(brier_score_loss(y_bin, p_risk)), 4)

    frac_pos, mean_pred = calibration_curve(y_bin, p_risk, n_bins=5, strategy="quantile")
    quantiles = np.quantile(p_risk, np.linspace(0.0, 1.0, len(mean_pred) + 1))
    bins: list[dict[str, Any]] = []
    for idx, (mp, fp) in enumerate(zip(mean_pred, frac_pos, strict=True)):
        lo, hi = quantiles[idx], quantiles[idx + 1]
        in_bin = (p_risk >= lo) & (p_risk <= hi if idx == len(mean_pred) - 1 else p_risk < hi)
        bins.append({
            "bin_mean_pred": round(float(mp), 4),
            "bin_true_freq": round(float(fp), 4),
            "bin_count": int(in_bin.sum()),
        })
    return brier, bins


def _extract_feature_importances(clf: Any, feature_names: list[str]) -> list[dict[str, Any]]:
    if hasattr(clf, "feature_importances_"):
        raw = np.asarray(clf.feature_importances_, dtype=float)
    elif isinstance(clf, Pipeline) and hasattr(clf.named_steps.get("clf"), "coef_"):
        raw = np.mean(np.abs(clf.named_steps["clf"].coef_), axis=0)
    else:
        raw = np.zeros(len(feature_names))
    total = float(np.sum(raw)) or 1.0
    items = [
        {"feature": n, "label": FEATURE_LABELS.get(n, n), "importance": round(float(v / total), 4)}
        for n, v in zip(feature_names, raw, strict=True)
    ]
    items.sort(key=lambda d: d["importance"], reverse=True)
    return items


def train_and_evaluate(artifacts_dir: Path | None = None) -> dict[str, Any]:
    """Train classifiers + regressor with 5-fold CV, calibration curve & holdout audit."""
    out_dir = Path(artifacts_dir or ARTIFACTS_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)

    raw_df = load_weekly_dataframe()
    feat_df = extract_features(raw_df, cutoff_week=CUTOFF_WEEK)
    tgt_df = compute_future_targets(raw_df, target_start_week=10)
    merged = feat_df.merge(tgt_df, on="student_id", how="inner")

    x_all = merged[FEATURE_NAMES].to_numpy(dtype=float)
    y_tier = merged["target_tier"].to_numpy()
    y_score = merged["target_score"].to_numpy()

    x_train, x_test, y_train, y_test, ys_train, ys_test = train_test_split(
        x_all, y_tier, y_score, test_size=0.25, stratify=y_tier, random_state=RANDOM_STATE
    )

    candidates: list[tuple[str, Any]] = [
        ("LogisticRegression", Pipeline([
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(max_iter=1000, random_state=RANDOM_STATE)),
        ])),
        ("RandomForestClassifier", RandomForestClassifier(
            n_estimators=200, max_depth=8, min_samples_leaf=2, random_state=RANDOM_STATE
        )),
        ("GradientBoostingClassifier", GradientBoostingClassifier(
            n_estimators=120, max_depth=3, learning_rate=0.08, random_state=RANDOM_STATE
        )),
    ]

    comparison: list[dict[str, Any]] = []
    fitted_models: dict[str, Any] = {}
    oof_map: dict[str, np.ndarray] = {}

    for name, clf in candidates:
        cv_metrics, oof_probs = _cross_validate_classifier(clf, x_all, y_tier)
        clf.fit(x_train, y_train)
        probs = clf.predict_proba(x_test)
        preds = np.argmax(probs, axis=1)
        comparison.append({
            "model_name": name,
            "at_risk_recall": round(
                float(
                    recall_score(
                        (y_test >= 2).astype(int), (preds >= 2).astype(int), zero_division=0
                    )
                ),
                4,
            ),
            "macro_f1": round(float(f1_score(y_test, preds, average="macro", zero_division=0)), 4),
            "roc_auc": round(
                float(roc_auc_score(y_test, probs, multi_class="ovr", average="macro")), 4
            ),
            "confusion_matrix": confusion_matrix(y_test, preds, labels=[0, 1, 2, 3]).tolist(),
            **cv_metrics,
        })
        fitted_models[name] = clf
        oof_map[name] = oof_probs

    best_entry = max(
        comparison, key=lambda m: (m["cv_at_risk_recall_mean"], m["cv_macro_f1_mean"])
    )
    best_name = best_entry["model_name"]
    best_clf = fitted_models[best_name]
    brier, calib_bins = _calibration_stats(y_tier, oof_map[best_name])

    regressor = GradientBoostingRegressor(
        n_estimators=120, max_depth=3, learning_rate=0.08, random_state=RANDOM_STATE
    )
    regressor.fit(x_train, ys_train)
    mae = float(mean_absolute_error(ys_test, np.clip(regressor.predict(x_test), 0.0, 100.0)))

    joblib.dump(best_clf, out_dir / "classifier.joblib")
    joblib.dump(regressor, out_dir / "regressor.joblib")
    np.save(out_dir / "shap_background.npy", x_train[:80])
    (out_dir / "feature_names.json").write_text(
        json.dumps(FEATURE_NAMES, indent=2), encoding="utf-8"
    )

    audit = {
        "selected_model": best_name,
        "feature_window_weeks": f"1-{CUTOFF_WEEK}",
        "target_window_weeks": "10-12",
        "train_size": len(x_train),
        "holdout_size": len(x_test),
        "class_labels": list(RISK_TIER_LABELS),
        "at_risk_recall": best_entry["at_risk_recall"],
        "macro_f1": best_entry["macro_f1"],
        "roc_auc": best_entry["roc_auc"],
        "mae": round(mae, 4),
        "brier_score": brier,
        "calibration_curve": calib_bins,
        "confusion_matrix": best_entry["confusion_matrix"],
        "model_comparison": comparison,
        "feature_importances": _extract_feature_importances(best_clf, FEATURE_NAMES),
    }
    (out_dir / "model_audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    reload_models(artifacts_dir=out_dir)
    return audit


if __name__ == "__main__":
    result = train_and_evaluate()
    print(f"Selected Classifier: {result['selected_model']} | Brier={result['brier_score']:.4f}")
    for row in result["model_comparison"]:
        print(
            f"  - {row['model_name']:26s} CV_recall={row['cv_at_risk_recall_mean']:.3f}"
            f"+-{row['cv_at_risk_recall_std']:.3f} holdout_auc={row['roc_auc']:.3f}"
        )
    print(f"Regressor Holdout MAE: {result['mae']:.3f}")
    print(f"Persisted {recompute_all_snapshots()} prediction snapshots")
