"""Single-query dashboard repository for Faculty KPIs, urgent queue, and triage matrix."""

from __future__ import annotations

from collections import Counter

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.snapshot import PredictionSnapshot
from app.models.student import Student
from app.repositories.snapshot_repo import extract_projected_score_after, get_active_week
from app.repositories.student_repo import to_student_summary
from app.schemas.dashboard import DashboardSummaryResponse, DistributionBucket, TriagePoint

TIER_ORDER = ["CRITICAL", "AT_RISK", "WATCH", "SAFE"]


def get_dashboard_summary(db: Session) -> DashboardSummaryResponse:
    """Compute cohort KPIs, distributions, urgent queue, and 240 triage dots in 1 SQL query."""
    settings = get_settings()
    stmt = (
        select(Student, PredictionSnapshot)
        .join(PredictionSnapshot, PredictionSnapshot.student_id == Student.id)
        .order_by(Student.id)
    )
    rows = db.execute(stmt).all()

    tier_counts: Counter[str] = Counter()
    arch_counts: Counter[str] = Counter()
    cusum_alerts = 0
    score_sum = 0.0
    summaries = []
    triage_points: list[TriagePoint] = []

    for stu, snap in rows:
        tier_counts[snap.risk_tier] += 1
        arch_counts[snap.archetype] += 1
        if snap.cusum_triggered:
            cusum_alerts += 1
        score_sum += float(snap.projected_final_score)

        proj_after = extract_projected_score_after(snap)
        summaries.append(to_student_summary(stu, snap))
        triage_points.append(
            TriagePoint(
                id=stu.id,
                roll_no=stu.roll_no,
                name=stu.name,
                risk_tier=snap.risk_tier,
                archetype=snap.archetype,
                risk_score=round(float(snap.risk_score), 2),
                ponr_days_left=int(snap.ponr_days_left),
                projected_final_score=round(float(snap.projected_final_score), 2),
                projected_score_after=round(proj_after, 2),
                rescue_gain=round(max(0.0, proj_after - float(snap.projected_final_score)), 2),
            )
        )

    total = len(rows)
    urgent_candidates = [s for s in summaries if s.risk_tier != "SAFE"]
    urgent_candidates.sort(key=lambda s: (s.ponr_days_left, -s.risk_score, s.id))

    risk_dist = [DistributionBucket(label=t, count=int(tier_counts.get(t, 0))) for t in TIER_ORDER]
    arch_dist = [
        DistributionBucket(label=k, count=v)
        for k, v in sorted(arch_counts.items(), key=lambda kv: -kv[1])
    ]

    active_week = get_active_week(db)
    return DashboardSummaryResponse(
        total_students=total,
        safe_count=int(tier_counts.get("SAFE", 0)),
        watch_count=int(tier_counts.get("WATCH", 0)),
        at_risk_count=int(tier_counts.get("AT_RISK", 0)),
        critical_count=int(tier_counts.get("CRITICAL", 0)),
        cusum_alerts_count=cusum_alerts,
        detention_cliff_count=int(arch_counts.get("DETENTION_CLIFF", 0)),
        passive_copier_count=int(arch_counts.get("PASSIVE_COPIER_CONCEPT_GAP", 0)),
        avg_projected_score=round(score_sum / total, 2) if total else 0.0,
        current_week=active_week,
        active_week=active_week,
        total_weeks=settings.TOTAL_WEEKS,
        risk_distribution=risk_dist,
        archetype_distribution=arch_dist,
        urgent_queue=urgent_candidates[:10],
        triage_points=triage_points,
    )
