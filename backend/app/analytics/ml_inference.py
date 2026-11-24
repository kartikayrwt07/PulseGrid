"""
Runtime ML Inference & SHAP Attribution Engine.

Uses correlation-dependent LinearExplainer for linear pipelines to handle
feature multicollinearity cleanly, and aggregates raw SHAP into 5 domain buckets
while preserving exact additive sum invariance.
"""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import shap
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline

from app.analytics.features import FEATURE_LABELS, FEATURE_NAMES
from app.core.config import BACKEND_DIR

RISK_TIER_LABELS: tuple[str, ...] = ("SAFE", "WATCH", "AT_RISK", "CRITICAL")
DEFAULT_ARTIFACTS_DIR = Path(BACKEND_DIR) / "ml" / "artifacts"

SHAP_BUCKETS: list[tuple[str, str, tuple[str, ...]]] = [
    (
        "bucket_attendance",
        "Attendance & Eligibility",
        ("att_mean", "att_min", "att_recent_2w", "z_att_mean", "sub_75_att_count"),
    ),
    ("bucket_ponr", "Detention Margin (PONR)", ("min_bunk_budget",)),
    (
        "bucket_internals",
        "Internal Assessment Performance",
        (
            "internal_mean",
            "internal_min",
            "internal_recent_2w",
            "z_internal_mean",
            "sub_40_ia_count",
        ),
    ),
    (
        "bucket_trajectory",
        "Trajectory & Silent Slip",
        (
            "v_composite_latest",
            "a_composite_latest",
            "cusum_triggered",
            "cusum_shift_magnitude",
            "ewma_flagged_count",
        ),
    ),
    (
        "bucket_divergence",
        "Assignment-Exam Gap",
        ("assign_mean", "assign_recent_2w", "z_assign_mean", "divergence_index"),
    ),
]


class _ModelRegistry:
    """Thread-safe singleton holder for loaded ML models and SHAP explainer."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._artifacts_dir: Path | None = None
        self.classifier: Any = None
        self.regressor: Any = None
        self.feature_names: list[str] = list(FEATURE_NAMES)
        self.model_audit: dict[str, Any] = {}
        self.background: np.ndarray | None = None
        self.shap_explainer: Any = None
        self.explainer_kind: str = "none"

    def ensure_loaded(
        self, artifacts_dir: Path | None = None, force_reload: bool = False
    ) -> None:
        target_dir = Path(artifacts_dir or DEFAULT_ARTIFACTS_DIR)
        with self._lock:
            if (
                not force_reload
                and self.classifier is not None
                and self._artifacts_dir == target_dir
            ):
                return
            clf_path = target_dir / "classifier.joblib"
            reg_path = target_dir / "regressor.joblib"
            feat_path = target_dir / "feature_names.json"
            audit_path = target_dir / "model_audit.json"
            bg_path = target_dir / "shap_background.npy"

            if not clf_path.exists() or not reg_path.exists():
                raise FileNotFoundError(
                    f"ML artifacts not found in {target_dir}. Run ml/train_and_evaluate.py first."
                )

            self.classifier = joblib.load(clf_path)
            self.regressor = joblib.load(reg_path)
            self.feature_names = (
                json.loads(feat_path.read_text(encoding="utf-8"))
                if feat_path.exists()
                else list(FEATURE_NAMES)
            )
            self.model_audit = (
                json.loads(audit_path.read_text(encoding="utf-8"))
                if audit_path.exists()
                else {}
            )
            self.background = np.load(bg_path) if bg_path.exists() else None
            self.shap_explainer, self.explainer_kind = _build_shap_explainer(
                self.classifier, self.background
            )
            self._artifacts_dir = target_dir

    def is_loaded(self, artifacts_dir: Path | None = None) -> bool:
        target_dir = Path(artifacts_dir or DEFAULT_ARTIFACTS_DIR)
        return self.classifier is not None and (target_dir / "classifier.joblib").exists()

    def clear(self) -> None:
        with self._lock:
            self.classifier = None
            self.regressor = None
            self.shap_explainer = None
            self.background = None
            self._artifacts_dir = None


_registry = _ModelRegistry()


def _build_shap_explainer(classifier: Any, background: np.ndarray | None) -> tuple[Any, str]:
    """Select the most accurate SHAP explainer preserving multicollinearity semantics."""
    if isinstance(classifier, RandomForestClassifier):
        return shap.TreeExplainer(classifier), "tree_rf"
    if isinstance(classifier, Pipeline) and "clf" in classifier.named_steps:
        bg = background if background is not None else np.zeros((1, len(FEATURE_NAMES)))
        scaled_bg = classifier[:-1].transform(bg)
        clf_step = classifier.named_steps["clf"]
        try:
            # correlation_dependent needs 1D coef; combine AT_RISK + CRITICAL logits
            if getattr(clf_step, "coef_", np.empty((0,))).ndim == 2 and len(clf_step.coef_) >= 4:
                risk_coef = np.asarray(clf_step.coef_[2] + clf_step.coef_[3], dtype=float)
                risk_bias = float(clf_step.intercept_[2] + clf_step.intercept_[3])
                model_1d: Any = (risk_coef, risk_bias)
            else:
                model_1d = clf_step
            exp = shap.LinearExplainer(
                model_1d,
                scaled_bg,
                nsamples=300,
                feature_perturbation="correlation_dependent",
            )
            return exp, "linear_pipe"
        except (np.linalg.LinAlgError, ValueError, IndexError):
            return shap.LinearExplainer(clf_step, scaled_bg), "linear_pipe"
    bg = background if background is not None else np.zeros((1, len(FEATURE_NAMES)))
    return shap.Explainer(
        lambda x: classifier.predict_proba(np.asarray(x, dtype=float))[:, 2:].sum(axis=1), bg
    ), "permutation"


def _to_feature_array(
    features: dict[str, float] | pd.Series | pd.DataFrame | np.ndarray,
    feature_names: list[str],
) -> np.ndarray:
    if isinstance(features, pd.DataFrame):
        return features[feature_names].to_numpy(dtype=float)
    if isinstance(features, pd.Series):
        return np.asarray([[float(features[n]) for n in feature_names]], dtype=float)
    if isinstance(features, dict):
        return np.asarray([[float(features.get(n, 0.0)) for n in feature_names]], dtype=float)
    arr = np.asarray(features, dtype=float)
    return arr.reshape(1, -1) if arr.ndim == 1 else arr


def reload_models(artifacts_dir: Path | None = None) -> None:
    _registry.ensure_loaded(artifacts_dir=artifacts_dir, force_reload=True)


def is_model_loaded(artifacts_dir: Path | None = None) -> bool:
    target = Path(artifacts_dir or DEFAULT_ARTIFACTS_DIR)
    return _registry.is_loaded(target) or (target / "classifier.joblib").exists()


def get_model_audit(artifacts_dir: Path | None = None) -> dict[str, Any]:
    _registry.ensure_loaded(artifacts_dir=artifacts_dir)
    return dict(_registry.model_audit)


def predict_risk(
    features: dict[str, float] | pd.Series | pd.DataFrame | np.ndarray,
    artifacts_dir: Path | None = None,
) -> dict[str, Any]:
    _registry.ensure_loaded(artifacts_dir=artifacts_dir)
    x_arr = _to_feature_array(features, _registry.feature_names)
    probs = _registry.classifier.predict_proba(x_arr)[0]
    tier_idx = int(np.argmax(probs))
    risk_score = float(np.dot(probs, np.array([0.0, 35.0, 72.0, 100.0])))
    projected = float(np.clip(_registry.regressor.predict(x_arr)[0], 0.0, 100.0))
    return {
        "risk_tier_idx": tier_idx,
        "risk_tier": RISK_TIER_LABELS[tier_idx],
        "risk_score": round(risk_score, 2),
        "at_risk_probability": round(float(probs[2] + probs[3]), 4),
        "class_probabilities": {
            lbl: round(float(p), 4) for lbl, p in zip(RISK_TIER_LABELS, probs, strict=True)
        },
        "projected_final_score": round(projected, 2),
    }


def predict_batch(
    features_df: pd.DataFrame | np.ndarray, artifacts_dir: Path | None = None
) -> tuple[np.ndarray, np.ndarray]:
    _registry.ensure_loaded(artifacts_dir=artifacts_dir)
    x_arr = (
        features_df[_registry.feature_names].to_numpy(dtype=float)
        if isinstance(features_df, pd.DataFrame)
        else np.asarray(features_df, dtype=float)
    )
    return _registry.classifier.predict_proba(x_arr), np.clip(
        _registry.regressor.predict(x_arr), 0.0, 100.0
    )


def get_shap_values(
    features: dict[str, float] | pd.Series | pd.DataFrame | np.ndarray,
    top_k: int = 8,
    artifacts_dir: Path | None = None,
) -> list[dict[str, Any]]:
    """Return sorted per-feature SHAP contributions toward P(AT_RISK or CRITICAL)."""
    _registry.ensure_loaded(artifacts_dir=artifacts_dir)
    x_arr = _to_feature_array(features, _registry.feature_names)
    kind = _registry.explainer_kind

    if kind == "tree_rf":
        sv = np.asarray(_registry.shap_explainer.shap_values(x_arr))
        risk_shap = sv[0, :, 2] + sv[0, :, 3]
    elif kind == "linear_pipe":
        scaled_x = _registry.classifier[:-1].transform(x_arr)
        sv = np.asarray(_registry.shap_explainer.shap_values(scaled_x))
        risk_shap = sv[0, :, 2] + sv[0, :, 3] if sv.ndim == 3 else sv[0]
    else:
        risk_shap = np.asarray(_registry.shap_explainer(x_arr).values)[0]

    entries = [
        {
            "feature": name,
            "label": FEATURE_LABELS.get(name, name),
            "shap_value": round(float(s_val), 6),
            "feature_value": round(float(x_arr[0][i]), 4),
        }
        for i, (name, s_val) in enumerate(zip(_registry.feature_names, risk_shap, strict=True))
    ]
    entries.sort(key=lambda item: abs(item["shap_value"]), reverse=True)
    return entries[:top_k] if top_k > 0 else entries


def group_shap_entries(raw_entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Sum exact raw SHAP attributions into 5 human-readable domain buckets."""
    by_feat = {item["feature"]: item for item in raw_entries}
    grouped: list[dict[str, Any]] = []
    for key, label, members in SHAP_BUCKETS:
        shap_sum = sum(float(by_feat.get(m, {}).get("shap_value", 0.0)) for m in members)
        rep_val = float(by_feat.get(members[0], {}).get("feature_value", 0.0))
        grouped.append({
            "feature": key,
            "label": label,
            "shap_value": round(shap_sum, 6),
            "feature_value": round(rep_val, 4),
        })
    grouped.sort(key=lambda item: abs(item["shap_value"]), reverse=True)
    return grouped


def get_grouped_and_raw_shap(
    features: dict[str, float] | pd.Series | pd.DataFrame | np.ndarray,
    artifacts_dir: Path | None = None,
) -> dict[str, list[dict[str, Any]]]:
    raw_all = get_shap_values(features, top_k=0, artifacts_dir=artifacts_dir)
    return {"grouped_shap": group_shap_entries(raw_all), "raw_shap": raw_all}
