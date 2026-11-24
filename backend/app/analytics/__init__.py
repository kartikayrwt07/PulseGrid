"""
Phase 2 analytics package — pure, stateless, zero-database math functions.
All functions accept plain Python / NumPy / Pandas structures only.
"""

from app.analytics.archetype import diagnose_archetype
from app.analytics.cusum import detect_cusum
from app.analytics.divergence import compute_divergence
from app.analytics.ponr import assess_internal_standing, calculate_subject_ponr
from app.analytics.zscore import compute_cohort_zscores, get_student_weekly_composite

__all__ = [
    "assess_internal_standing",
    "calculate_subject_ponr",
    "compute_cohort_zscores",
    "compute_divergence",
    "detect_cusum",
    "diagnose_archetype",
    "get_student_weekly_composite",
]
