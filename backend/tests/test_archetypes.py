"""Tests for the 5-Archetype Academic Diagnoser."""


from app.analytics.archetype import (
    ARCHETYPES,
    diagnose_archetype,
    diagnose_archetypes,
)

# ---------------------------------------------------------------------------
# Shared test helpers
# ---------------------------------------------------------------------------

def _build_safe_ponr() -> list[dict]:
    return [{"eligibility_status": "SAFE"} for _ in range(5)]


def _build_cliff_ponr(subject_index: int = 0, status: str = "WINDOW_CLOSING") -> list[dict]:
    ponr = _build_safe_ponr()
    ponr[subject_index]["eligibility_status"] = status
    return ponr


def _safe_divergence() -> dict:
    return {"divergence_index": 0.3, "flagged": False}


def _safe_cusum() -> dict:
    return {"change_point_detected": False, "change_point_week": None}


def _build_subject_z(n: int, z_att: float, z_internal: float) -> list[dict]:
    return [{"z_att_mean": z_att, "z_internal_mean": z_internal} for _ in range(n)]


# ---------------------------------------------------------------------------
# Priority 1: DETENTION_CLIFF
# ---------------------------------------------------------------------------

def test_detention_cliff_window_closing():
    result = diagnose_archetype(
        ponr_results=_build_cliff_ponr(0, "WINDOW_CLOSING"),
        divergence_result=_safe_divergence(),
        cusum_result=_safe_cusum(),
        z_composite_recent=-2.0,
        subject_z_summary=_build_subject_z(5, -1.5, -1.5),
        z_internal_avg=-1.5,
        z_att_avg=-1.5,
    )
    assert result == "DETENTION_CLIFF"


def test_detention_cliff_unrecoverable():
    result = diagnose_archetype(
        ponr_results=_build_cliff_ponr(1, "UNRECOVERABLE_WITHOUT_WAIVER"),
        divergence_result={"divergence_index": 2.5, "flagged": True},  # also passive copier
        cusum_result={"change_point_detected": True, "change_point_week": 6},
        z_composite_recent=-2.5,
        subject_z_summary=_build_subject_z(5, -1.5, -1.5),
        z_internal_avg=-1.5,
        z_att_avg=-1.5,
    )
    # DETENTION_CLIFF beats PASSIVE_COPIER (priority 1 > priority 2)
    assert result == "DETENTION_CLIFF"


# ---------------------------------------------------------------------------
# Priority 2: PASSIVE_COPIER_CONCEPT_GAP
# ---------------------------------------------------------------------------

def test_passive_copier_flagged():
    result = diagnose_archetype(
        ponr_results=_build_safe_ponr(),
        divergence_result={"divergence_index": 2.0, "flagged": True},
        cusum_result=_safe_cusum(),
        z_composite_recent=0.5,
        subject_z_summary=_build_subject_z(5, 0.5, -0.3),
        z_internal_avg=-0.3,
        z_att_avg=0.5,
    )
    assert result == "PASSIVE_COPIER_CONCEPT_GAP"


def test_passive_copier_beats_silent_slipper():
    """When both conditions met, PASSIVE_COPIER wins over SILENT_SLIPPER."""
    result = diagnose_archetype(
        ponr_results=_build_safe_ponr(),
        divergence_result={"divergence_index": 2.0, "flagged": True},
        cusum_result={"change_point_detected": True, "change_point_week": 6},
        z_composite_recent=-1.5,
        subject_z_summary=_build_subject_z(5, 0.0, -0.5),
        z_internal_avg=-0.5,
        z_att_avg=0.0,
    )
    assert result == "PASSIVE_COPIER_CONCEPT_GAP"


# ---------------------------------------------------------------------------
# Priority 3: SILENT_SLIPPER
# ---------------------------------------------------------------------------

def test_silent_slipper_detected():
    result = diagnose_archetype(
        ponr_results=_build_safe_ponr(),
        divergence_result=_safe_divergence(),
        cusum_result={"change_point_detected": True, "change_point_week": 7},
        z_composite_recent=-1.5,
        subject_z_summary=_build_subject_z(5, -0.3, -0.5),
        z_internal_avg=-0.5,
        z_att_avg=-0.3,
    )
    assert result == "SILENT_SLIPPER"


def test_silent_slipper_requires_negative_recent_z():
    """CUSUM alone without negative recent Z should not classify as SILENT_SLIPPER."""
    result = diagnose_archetype(
        ponr_results=_build_safe_ponr(),
        divergence_result=_safe_divergence(),
        cusum_result={"change_point_detected": True, "change_point_week": 5},
        z_composite_recent=0.5,  # still positive — recovered?
        subject_z_summary=_build_subject_z(5, 0.0, 0.0),
        z_internal_avg=0.0,
        z_att_avg=0.0,
    )
    assert result != "SILENT_SLIPPER"


# ---------------------------------------------------------------------------
# Priority 4: BROAD_DISENGAGEMENT
# ---------------------------------------------------------------------------

def test_broad_disengagement_3_subjects():
    result = diagnose_archetype(
        ponr_results=_build_safe_ponr(),
        divergence_result=_safe_divergence(),
        cusum_result=_safe_cusum(),
        z_composite_recent=-1.2,
        subject_z_summary=[
            {"z_att_mean": -1.5, "z_internal_mean": -1.5},
            {"z_att_mean": -1.2, "z_internal_mean": -1.3},
            {"z_att_mean": -1.1, "z_internal_mean": -1.4},
            {"z_att_mean": 0.5, "z_internal_mean": 0.3},  # fine
            {"z_att_mean": 0.2, "z_internal_mean": 0.1},  # fine
        ],
        z_internal_avg=-0.78,
        z_att_avg=-0.62,
    )
    assert result == "BROAD_DISENGAGEMENT"


def test_broad_disengagement_needs_3_subjects():
    """Only 2 subjects failing — should NOT trigger BROAD_DISENGAGEMENT."""
    result = diagnose_archetype(
        ponr_results=_build_safe_ponr(),
        divergence_result=_safe_divergence(),
        cusum_result=_safe_cusum(),
        z_composite_recent=-0.8,
        subject_z_summary=[
            {"z_att_mean": -1.5, "z_internal_mean": -1.5},
            {"z_att_mean": -1.2, "z_internal_mean": -1.3},
            {"z_att_mean": 0.5, "z_internal_mean": 0.3},
            {"z_att_mean": 0.2, "z_internal_mean": 0.1},
            {"z_att_mean": 0.4, "z_internal_mean": 0.2},
        ],
        z_internal_avg=-0.46,
        z_att_avg=-0.26,
    )
    assert result != "BROAD_DISENGAGEMENT"


# ---------------------------------------------------------------------------
# Priority 5: CONCEPTUAL_STRUGGLER
# ---------------------------------------------------------------------------

def test_conceptual_struggler():
    result = diagnose_archetype(
        ponr_results=_build_safe_ponr(),
        divergence_result=_safe_divergence(),
        cusum_result=_safe_cusum(),
        z_composite_recent=-0.5,
        subject_z_summary=_build_subject_z(5, 0.1, -1.2),
        z_internal_avg=-1.2,
        z_att_avg=0.1,  # attendance OK (≥ -0.5)
    )
    assert result == "CONCEPTUAL_STRUGGLER"


# ---------------------------------------------------------------------------
# ON_TRACK — no signals
# ---------------------------------------------------------------------------

def test_on_track():
    result = diagnose_archetype(
        ponr_results=_build_safe_ponr(),
        divergence_result=_safe_divergence(),
        cusum_result=_safe_cusum(),
        z_composite_recent=0.5,
        subject_z_summary=_build_subject_z(5, 0.3, 0.2),
        z_internal_avg=0.2,
        z_att_avg=0.3,
    )
    assert result == "ON_TRACK"


# ---------------------------------------------------------------------------
# All archetypes are known values
# ---------------------------------------------------------------------------

def test_archetype_values_are_valid():
    assert set(ARCHETYPES) == {
        "DETENTION_CLIFF",
        "PASSIVE_COPIER_CONCEPT_GAP",
        "SILENT_SLIPPER",
        "BROAD_DISENGAGEMENT",
        "CONCEPTUAL_STRUGGLER",
        "ON_TRACK",
    }


def test_multi_label_compound_detention_and_silent_slip():
    result = diagnose_archetypes(
        ponr_results=_build_cliff_ponr(0, "WINDOW_CLOSING"),
        divergence_result=_safe_divergence(),
        cusum_result={"change_point_detected": True, "change_point_week": 7},
        z_composite_recent=-1.5,
        subject_z_summary=_build_subject_z(5, -0.8, -0.7),
        z_internal_avg=-0.7,
        z_att_avg=-0.8,
    )
    assert result["primary_archetype"] == "DETENTION_CLIFF"
    assert "SILENT_SLIPPER" in result["secondary_flags"]


def test_multi_label_on_track_has_no_secondary_flags():
    result = diagnose_archetypes(
        ponr_results=_build_safe_ponr(),
        divergence_result=_safe_divergence(),
        cusum_result=_safe_cusum(),
        z_composite_recent=0.5,
        subject_z_summary=_build_subject_z(5, 0.3, 0.2),
        z_internal_avg=0.2,
        z_att_avg=0.3,
    )
    assert result["primary_archetype"] == "ON_TRACK"
    assert result["secondary_flags"] == []
