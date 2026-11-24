"""
Fuzzy CSV/XLSX Column Auto-Mapper & Data-Health Inspector.

Uses stdlib ``difflib.SequenceMatcher`` plus domain synonyms to align messy
spreadsheet headers (e.g. ``Take-Home Assn (%)`` -> ``assignment_score``) to
canonical PulseGrid fields with explicit confidence scores.
"""

from __future__ import annotations

from difflib import SequenceMatcher

import pandas as pd

from app.schemas.upload import ColumnMappingEntry

REQUIRED_CANONICAL: list[str] = [
    "roll_no",
    "student_name",
    "subject_code",
    "week",
    "attended_sessions",
    "total_sessions",
    "assignment_score",
    "internal_score",
]

COLUMN_SYNONYMS: dict[str, tuple[str, ...]] = {
    "roll_no": ("rollno", "rollnumber", "studentroll", "roll", "regno", "studentid"),
    "student_name": ("studentname", "fullname", "learnername", "name"),
    "subject_code": ("subjectcode", "coursecode", "subjectid", "subject", "course"),
    "week": ("week", "wk", "weekno", "weeknumber"),
    "attended_sessions": ("attendedsessions", "classesattended", "attended", "present"),
    "total_sessions": ("totalsessions", "totalclasses", "scheduledsessions", "sessions"),
    "assignment_score": ("assignmentscore", "takehomeassn", "assignments", "assignment", "hw"),
    "internal_score": (
        "internalscore",
        "midterminternalmarks",
        "internalmarks",
        "internals",
        "midterm",
        "ia",
    ),
}


def normalize_header(raw: str) -> str:
    return "".join(ch for ch in raw.lower() if ch.isalnum())


def _score_candidate(norm_source: str, canonical: str) -> float:
    canon_norm = canonical.replace("_", "")
    if norm_source == canon_norm:
        return 1.0
    synonyms = COLUMN_SYNONYMS.get(canonical, ())
    if norm_source in synonyms:
        return 0.94
    best = SequenceMatcher(None, norm_source, canon_norm).ratio()
    for syn in synonyms:
        if len(syn) >= 4 and syn in norm_source:
            best = max(best, 0.86)
        else:
            best = max(best, SequenceMatcher(None, norm_source, syn).ratio())
    return best


def map_columns_fuzzy(
    columns: list[str], min_confidence: float = 0.62
) -> tuple[list[ColumnMappingEntry], dict[str, str]]:
    """Map raw spreadsheet headers to canonical columns with confidence scores."""
    scored_pairs: list[tuple[float, str, str]] = []
    for raw_col in columns:
        norm = normalize_header(raw_col)
        if not norm:
            continue
        for canonical in REQUIRED_CANONICAL:
            score = _score_candidate(norm, canonical)
            if score >= min_confidence:
                scored_pairs.append((score, raw_col, canonical))

    # Greedy highest-confidence 1-to-1 assignment prevents duplicate target collisions
    scored_pairs.sort(key=lambda item: item[0], reverse=True)
    rename_map: dict[str, str] = {}
    used_sources: set[str] = set()
    used_targets: set[str] = set()
    conf_map: dict[str, float] = {}

    for score, raw_col, canonical in scored_pairs:
        if raw_col in used_sources or canonical in used_targets:
            continue
        used_sources.add(raw_col)
        used_targets.add(canonical)
        rename_map[raw_col] = canonical
        conf_map[raw_col] = round(score, 2)

    entries: list[ColumnMappingEntry] = []
    for raw_col in columns:
        target = rename_map.get(raw_col)
        entries.append(
            ColumnMappingEntry(
                source_column=raw_col,
                canonical_column=target,
                confidence=conf_map.get(raw_col, 0.0),
                status="mapped" if target else "unmapped",
            )
        )
    return entries, rename_map


def inspect_data_health(df: pd.DataFrame) -> list[str]:
    """Scan mapped DataFrame for out-of-range marks, attendance anomalies, or NaNs."""
    warnings: list[str] = []
    missing_req = [c for c in REQUIRED_CANONICAL if c not in df.columns]
    if missing_req:
        warnings.append(f"Missing required canonical columns: {', '.join(missing_req)}")

    for col in ("assignment_score", "internal_score"):
        if col in df.columns:
            series = pd.to_numeric(df[col], errors="coerce")
            invalid_cnt = int(((series < 0) | (series > 100)).sum())
            if invalid_cnt > 0:
                warnings.append(f"{invalid_cnt} row(s) have out-of-range {col} outside 0-100.")
            na_cnt = int(series.isna().sum())
            if na_cnt > 0:
                warnings.append(f"{na_cnt} row(s) have non-numeric or missing {col}.")

    if "attended_sessions" in df.columns and "total_sessions" in df.columns:
        att = pd.to_numeric(df["attended_sessions"], errors="coerce")
        tot = pd.to_numeric(df["total_sessions"], errors="coerce")
        bad_att = int(((att < 0) | (tot <= 0) | (att > tot)).sum())
        if bad_att > 0:
            warnings.append(
                f"{bad_att} row(s) have attended_sessions exceeding total_sessions or <= 0 total."
            )
    return warnings
