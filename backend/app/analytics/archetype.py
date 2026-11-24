"""
Multi-Label 5-Archetype Academic Diagnoser.

Evaluates ALL root-cause conditions in priority order:
  1. DETENTION_CLIFF
  2. PASSIVE_COPIER_CONCEPT_GAP
  3. SILENT_SLIPPER
  4. BROAD_DISENGAGEMENT
  5. CONCEPTUAL_STRUGGLER
  0. ON_TRACK

Returns primary_archetype (highest priority) + secondary_flags (all other
triggered root-cause archetypes) so compound students do not lose secondary flags.
"""

from __future__ import annotations

ARCHETYPES = [
    "DETENTION_CLIFF",
    "PASSIVE_COPIER_CONCEPT_GAP",
    "SILENT_SLIPPER",
    "BROAD_DISENGAGEMENT",
    "CONCEPTUAL_STRUGGLER",
    "ON_TRACK",
]

DIVERGENCE_THRESHOLD = 1.5
Z_CONCERN_THRESHOLD = -1.0
BROAD_SUBJECT_COUNT = 3
CUSUM_Z_RECENT_THRESHOLD = -1.0


def _is_detention_cliff(ponr_results: list[dict]) -> bool:
    danger_statuses = {"WINDOW_CLOSING", "UNRECOVERABLE_WITHOUT_WAIVER"}
    return any(r.get("eligibility_status") in danger_statuses for r in ponr_results)


def _is_passive_copier(divergence_result: dict) -> bool:
    return float(divergence_result.get("divergence_index", 0.0)) > DIVERGENCE_THRESHOLD


def _is_silent_slipper(cusum_result: dict, z_composite_recent: float) -> bool:
    return (
        bool(cusum_result.get("change_point_detected", False))
        and z_composite_recent < CUSUM_Z_RECENT_THRESHOLD
    )


def _is_broad_disengagement(subject_z_summary: list[dict]) -> bool:
    count = sum(
        1
        for s in subject_z_summary
        if s.get("z_att_mean", 0.0) < Z_CONCERN_THRESHOLD
        and s.get("z_internal_mean", 0.0) < Z_CONCERN_THRESHOLD
    )
    return count >= BROAD_SUBJECT_COUNT


def _is_conceptual_struggler(z_internal_avg: float, z_att_avg: float) -> bool:
    return z_internal_avg < Z_CONCERN_THRESHOLD and z_att_avg >= -0.5


def diagnose_archetypes(
    ponr_results: list[dict],
    divergence_result: dict,
    cusum_result: dict,
    z_composite_recent: float,
    subject_z_summary: list[dict],
    z_internal_avg: float,
    z_att_avg: float,
) -> dict[str, str | list[str]]:
    """
    Evaluate all diagnostic rules and return:
        {"primary_archetype": str, "secondary_flags": list[str]}
    """
    matched: list[str] = []
    if _is_detention_cliff(ponr_results):
        matched.append("DETENTION_CLIFF")
    if _is_passive_copier(divergence_result):
        matched.append("PASSIVE_COPIER_CONCEPT_GAP")
    if _is_silent_slipper(cusum_result, z_composite_recent):
        matched.append("SILENT_SLIPPER")
    if _is_broad_disengagement(subject_z_summary):
        matched.append("BROAD_DISENGAGEMENT")
    if _is_conceptual_struggler(z_internal_avg, z_att_avg):
        matched.append("CONCEPTUAL_STRUGGLER")

    if not matched:
        return {"primary_archetype": "ON_TRACK", "secondary_flags": []}
    return {"primary_archetype": matched[0], "secondary_flags": matched[1:]}


def diagnose_archetype(
    ponr_results: list[dict],
    divergence_result: dict,
    cusum_result: dict,
    z_composite_recent: float,
    subject_z_summary: list[dict],
    z_internal_avg: float,
    z_att_avg: float,
) -> str:
    """Backward-compatible single primary-archetype wrapper."""
    res = diagnose_archetypes(
        ponr_results=ponr_results,
        divergence_result=divergence_result,
        cusum_result=cusum_result,
        z_composite_recent=z_composite_recent,
        subject_z_summary=subject_z_summary,
        z_internal_avg=z_internal_avg,
        z_att_avg=z_att_avg,
    )
    return str(res["primary_archetype"])
