"""Anti-leakage tests verifying strict feature hygiene and temporal cutoffs."""

import json
import sqlite3
from pathlib import Path

import pandas as pd

from app.analytics.features import FEATURE_NAMES, extract_features
from app.analytics.ml_inference import DEFAULT_ARTIFACTS_DIR
from app.core.config import BACKEND_DIR

FORBIDDEN_TOKENS = ("final", "exam_score", "target", "persona", "outcome", "gender", "age", "name")


def test_no_final_exam_features_in_artifacts():
    feat_path = Path(DEFAULT_ARTIFACTS_DIR) / "feature_names.json"
    assert feat_path.exists(), "feature_names.json missing — run train_and_evaluate.py"
    features = json.loads(feat_path.read_text(encoding="utf-8"))
    assert features == FEATURE_NAMES
    for feat in features:
        low = feat.lower()
        assert not any(tok in low for tok in FORBIDDEN_TOKENS), f"Leaky feature found: {feat}"


def test_temporal_cutoff_strictness_against_future_mutation():
    db_path = Path(BACKEND_DIR) / "pulsegrid.db"
    with sqlite3.connect(db_path) as conn:
        df = pd.read_sql(
            "SELECT w.*, s.sessions_per_week FROM weekly_records w "
            "JOIN subjects s ON s.id = w.subject_id WHERE w.student_id <= 20",
            conn,
        )

    baseline_features = extract_features(df, cutoff_week=8)

    # Wildly mutate all records after Week 8 — must NOT alter Weeks 1..8 features at all
    mutated = df.copy()
    mask_future = mutated["week"] > 8
    mutated.loc[mask_future, "attendance_pct"] = 0.0
    mutated.loc[mask_future, "assignment_score"] = 100.0
    mutated.loc[mask_future, "internal_score"] = 0.0

    after_mutation = extract_features(mutated, cutoff_week=8)
    pd.testing.assert_frame_equal(baseline_features, after_mutation)
