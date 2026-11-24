"""Tests for ML inference, SHAP explanations, and real holdout model_audit.json."""

import json
from pathlib import Path

import pytest

from app.analytics.features import FEATURE_NAMES
from app.analytics.ml_inference import (
    DEFAULT_ARTIFACTS_DIR,
    RISK_TIER_LABELS,
    get_grouped_and_raw_shap,
    get_model_audit,
    get_shap_values,
    is_model_loaded,
    predict_risk,
)


def _sample_feature_vector(high_risk: bool = False) -> dict[str, float]:
    if high_risk:
        return {
            "att_mean": 58.0,
            "att_min": 48.0,
            "att_recent_2w": 52.0,
            "assign_mean": 60.0,
            "assign_recent_2w": 55.0,
            "internal_mean": 46.0,
            "internal_min": 38.0,
            "internal_recent_2w": 42.0,
            "z_att_mean": -1.8,
            "z_assign_mean": -1.4,
            "z_internal_mean": -1.9,
            "v_composite_latest": -0.9,
            "a_composite_latest": -0.3,
            "divergence_index": 0.5,
            "cusum_triggered": 1.0,
            "cusum_shift_magnitude": 1.7,
            "ewma_flagged_count": 3.0,
            "min_bunk_budget": -1.0,
            "sub_75_att_count": 3.0,
            "sub_40_ia_count": 2.0,
        }
    return {
        "att_mean": 92.0,
        "att_min": 85.0,
        "att_recent_2w": 94.0,
        "assign_mean": 86.0,
        "assign_recent_2w": 88.0,
        "internal_mean": 84.0,
        "internal_min": 78.0,
        "internal_recent_2w": 85.0,
        "z_att_mean": 0.7,
        "z_assign_mean": 0.6,
        "z_internal_mean": 0.8,
        "v_composite_latest": 0.1,
        "a_composite_latest": 0.05,
        "divergence_index": -0.2,
        "cusum_triggered": 0.0,
        "cusum_shift_magnitude": 0.0,
        "ewma_flagged_count": 0.0,
        "min_bunk_budget": 9.0,
        "sub_75_att_count": 0.0,
        "sub_40_ia_count": 0.0,
    }


def test_artifacts_loaded():
    assert is_model_loaded() is True
    assert Path(DEFAULT_ARTIFACTS_DIR / "classifier.joblib").exists()
    assert Path(DEFAULT_ARTIFACTS_DIR / "regressor.joblib").exists()


def test_predict_risk_returns_valid_tier():
    res = predict_risk(_sample_feature_vector(high_risk=True))
    assert res["risk_tier_idx"] in (0, 1, 2, 3)
    assert res["risk_tier"] in RISK_TIER_LABELS
    assert 0.0 <= res["projected_final_score"] <= 100.0
    assert res["risk_tier"] in ("AT_RISK", "CRITICAL")


def test_predict_safe_student_is_low_risk():
    res = predict_risk(_sample_feature_vector(high_risk=False))
    assert res["risk_tier"] in ("SAFE", "WATCH")
    assert res["projected_final_score"] > 70.0


def test_get_shap_values_sorted_and_valid():
    shap_entries = get_shap_values(_sample_feature_vector(high_risk=True), top_k=8)
    assert len(shap_entries) == 8
    mags = [abs(item["shap_value"]) for item in shap_entries]
    assert mags == sorted(mags, reverse=True)
    for item in shap_entries:
        assert item["feature"] in FEATURE_NAMES
        assert "label" in item


def test_model_audit_has_real_metrics():
    audit_path = Path(DEFAULT_ARTIFACTS_DIR) / "model_audit.json"
    assert audit_path.exists()
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    for key in (
        "at_risk_recall",
        "macro_f1",
        "roc_auc",
        "mae",
        "confusion_matrix",
        "brier_score",
        "calibration_curve",
    ):
        assert key in audit
    assert 2.5 <= audit["mae"] <= 6.5
    assert audit["roc_auc"] >= 0.85
    assert audit["at_risk_recall"] >= 0.85
    assert 0.0 <= audit["brier_score"] <= 0.35
    assert len(audit["calibration_curve"]) >= 3
    for row in audit["model_comparison"]:
        assert row["cv_at_risk_recall_mean"] > 0.0
    assert audit["model_comparison"][0]["cv_at_risk_recall_mean"] >= 0.0
    assert get_model_audit()["selected_model"] == audit["selected_model"]


def test_grouped_shap_preserves_additive_invariance():
    bundle = get_grouped_and_raw_shap(_sample_feature_vector(high_risk=True))
    grouped = bundle["grouped_shap"]
    raw = bundle["raw_shap"]
    assert len(grouped) == 5
    assert len(raw) == len(FEATURE_NAMES)
    raw_sum = sum(item["shap_value"] for item in raw)
    grouped_sum = sum(item["shap_value"] for item in grouped)
    assert grouped_sum == pytest.approx(raw_sum, abs=1e-4)
