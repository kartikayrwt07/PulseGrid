"""Tests for the Assignment–Internal Divergence Index."""

import pytest

from app.analytics.divergence import DIVERGENCE_THRESHOLD, compute_divergence
from app.analytics.zscore import compute_cohort_zscores

# ---------------------------------------------------------------------------
# Meera Nair — PASSIVE_COPIER_CONCEPT_GAP
# 94% assignments vs 39% internals in a cohort averaging ~80/78
# ---------------------------------------------------------------------------

def test_meera_divergence_flagged(meera_df):
    """Meera must have divergence_index > 1.5 and flagged=True."""
    scored_df = compute_cohort_zscores(meera_df)
    result = compute_divergence(scored_df, student_id=2)
    assert result["flagged"] is True, (
        f"Expected Meera flagged but divergence_index={result['divergence_index']:.3f}"
    )
    assert result["divergence_index"] > DIVERGENCE_THRESHOLD


def test_meera_z_assign_positive(meera_df):
    """Meera's assignment Z-score should be clearly positive (above cohort)."""
    scored_df = compute_cohort_zscores(meera_df)
    result = compute_divergence(scored_df, student_id=2)
    assert result["z_assign_avg"] > 1.0


def test_meera_z_internal_negative(meera_df):
    """Meera's internal Z-score should be clearly negative (below cohort)."""
    scored_df = compute_cohort_zscores(meera_df)
    result = compute_divergence(scored_df, student_id=2)
    assert result["z_internal_avg"] < -1.0


# ---------------------------------------------------------------------------
# Average student — no flag expected
# ---------------------------------------------------------------------------

def test_average_student_not_flagged(meera_df):
    """An average cohort student (student_id=10) should NOT be flagged."""
    scored_df = compute_cohort_zscores(meera_df)
    result = compute_divergence(scored_df, student_id=10)
    assert result["flagged"] is False
    assert abs(result["divergence_index"]) < DIVERGENCE_THRESHOLD


# ---------------------------------------------------------------------------
# Empty / missing student
# ---------------------------------------------------------------------------

def test_missing_student_returns_zero(meera_df):
    scored_df = compute_cohort_zscores(meera_df)
    result = compute_divergence(scored_df, student_id=999)
    assert result["divergence_index"] == 0.0
    assert result["flagged"] is False


def test_missing_z_columns_raises(meera_df):
    with pytest.raises(ValueError, match="z_assign"):
        compute_divergence(meera_df, student_id=2)  # no z_* cols yet
