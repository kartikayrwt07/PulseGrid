"""Tests for the CUSUM & EWMA Change-Point Detector."""


from app.analytics.cusum import compute_ewma, detect_cusum

# ---------------------------------------------------------------------------
# Aarav Kulkarni — SILENT_SLIPPER
# Baseline Weeks 1–4: composites ≈ [89.33, 90.33, 88.0, 89.33]
# Week 6 subtle dip (composite ≈ 87.0): S < h with h_factor=4.0
# Week 7 sharp drop (composite ≈ 58.7): S >> h → triggers at Week 7
# ---------------------------------------------------------------------------

def test_aarav_cusum_fires_week_7(aarav_weekly_composites):
    """CUSUM must detect change point at exactly Week 7 for Aarav's trajectory."""
    result = detect_cusum(aarav_weekly_composites, baseline_weeks=4, h_factor=4.0)
    assert result["change_point_detected"] is True, "CUSUM did not detect any change point"
    assert result["change_point_week"] == 7, (
        f"Expected change_point_week=7, got {result['change_point_week']}"
    )


def test_aarav_cusum_shift_magnitude_is_large(aarav_weekly_composites):
    """Shift magnitude at trigger must be large (sharp drop in Week 7)."""
    result = detect_cusum(aarav_weekly_composites, baseline_weeks=4, h_factor=4.0)
    assert result["shift_magnitude"] is not None
    assert result["shift_magnitude"] > 20.0, (
        f"Expected large shift, got {result['shift_magnitude']}"
    )


def test_cusum_does_not_trigger_during_stable_period():
    """Stable scores should never trigger CUSUM."""
    stable = [85.0, 86.0, 84.0, 85.0, 85.5, 84.5, 86.0, 85.0, 85.5]
    result = detect_cusum(stable, baseline_weeks=4)
    assert result["change_point_detected"] is False


def test_cusum_subtle_drop_does_not_trigger_at_week_6(aarav_weekly_composites):
    """Week 6 subtle dip alone must not trigger CUSUM with h_factor=4.0."""
    # Only pass weeks 1-6 (before the sharp drop)
    partial_series = aarav_weekly_composites[:6]
    result = detect_cusum(partial_series, baseline_weeks=4, h_factor=4.0)
    assert result["change_point_detected"] is False, (
        f"Week 6 subtle dip triggered CUSUM prematurely at week {result['change_point_week']}"
    )


def test_cusum_series_length_matches_input(aarav_weekly_composites):
    result = detect_cusum(aarav_weekly_composites, baseline_weeks=4)
    assert len(result["cusum_series"]) == len(aarav_weekly_composites)


def test_cusum_baseline_values_correct(aarav_weekly_composites):
    """Baseline mean and std should reflect Weeks 1–4 composites."""
    result = detect_cusum(aarav_weekly_composites, baseline_weeks=4)
    # Baseline: [89.33, 90.33, 88.0, 89.33]
    assert 88.0 < result["baseline_mean"] < 91.0
    assert result["baseline_std"] > 0.0


def test_cusum_too_short_series_returns_no_change():
    result = detect_cusum([85.0, 84.0], baseline_weeks=4)
    assert result["change_point_detected"] is False


# ---------------------------------------------------------------------------
# EWMA tests
# ---------------------------------------------------------------------------

def test_ewma_flags_sustained_drop(aarav_weekly_composites):
    """EWMA should flag weeks after the sharp drop."""
    result = compute_ewma(aarav_weekly_composites, baseline_weeks=4)
    # Weeks 7–9 (indices 6–8) should be flagged
    flagged = result["flagged_weeks"]
    assert any(w >= 7 for w in flagged), f"EWMA did not flag any weeks >= 7: {flagged}"


def test_ewma_stable_no_flags():
    stable = [82.0, 83.0, 81.0, 82.0, 82.5, 81.5, 82.0, 83.0, 82.5]
    result = compute_ewma(stable, baseline_weeks=4)
    assert result["flagged_weeks"] == []


def test_ewma_series_length(aarav_weekly_composites):
    result = compute_ewma(aarav_weekly_composites, baseline_weeks=4)
    assert len(result["ewma_series"]) == len(aarav_weekly_composites)
