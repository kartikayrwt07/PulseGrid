"""CSV/XLSX academic records upload and fuzzy column mapping preview endpoint."""

from __future__ import annotations

import io
from pathlib import Path
from zipfile import BadZipFile

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.core.auth import TokenPayload
from app.core.database import get_db
from app.core.dependencies import require_faculty
from app.schemas.upload import UploadResult
from app.services.csv_mapper import (
    REQUIRED_CANONICAL,
    inspect_data_health,
    map_columns_fuzzy,
)
from app.services.upload_ingest import commit_uploaded_records

router = APIRouter(prefix="/upload", tags=["upload"])

MAX_UPLOAD_BYTES = 5 * 1024 * 1024
ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}


def _parse_upload_dataframe(filename: str, raw_bytes: bytes) -> pd.DataFrame:
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{ext}'. Allowed: .csv, .xlsx, .xls.",
        )
    if not raw_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty."
        )
    if len(raw_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File exceeds 5 MB maximum upload limit.",
        )

    parse_errors = (
        UnicodeDecodeError,
        ValueError,
        pd.errors.ParserError,
        pd.errors.EmptyDataError,
        BadZipFile,
    )
    try:
        if ext == ".csv":
            df = pd.read_csv(io.BytesIO(raw_bytes))
        else:
            df = pd.read_excel(io.BytesIO(raw_bytes), engine="openpyxl")
    except parse_errors as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Could not parse file contents. Ensure valid CSV or Excel formatting.",
        ) from exc

    if df.empty or len(df.columns) == 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Uploaded table contains no data rows.",
        )
    return df


@router.post("/csv", response_model=UploadResult)
async def upload_academic_file(
    file: UploadFile = File(...),
    commit: bool = Query(default=False),
    _faculty: TokenPayload = Depends(require_faculty),
    db: Session = Depends(get_db),
) -> UploadResult:
    """Parse CSV/XLSX cohort sheet for preview or transactional commit (commit=true)."""
    safe_name = Path(file.filename or "upload.csv").name
    raw_bytes = await file.read()
    df = _parse_upload_dataframe(safe_name, raw_bytes)

    mappings, rename_map = map_columns_fuzzy([str(c) for c in df.columns])
    normalized_df = df.rename(columns=rename_map)
    missing_req = [c for c in REQUIRED_CANONICAL if c not in normalized_df.columns]
    warnings = inspect_data_health(normalized_df)

    valid_rows = int(normalized_df.dropna(how="all").shape[0])
    preview_df = normalized_df.head(10).where(pd.notnull(normalized_df), None)
    preview_rows = [
        {str(k): (v.item() if hasattr(v, "item") else v) for k, v in row.items()}
        for row in preview_df.to_dict(orient="records")
    ]

    if not commit:
        return UploadResult(
            filename=safe_name,
            row_count=len(df),
            valid_row_count=valid_rows,
            missing_required=missing_req,
            column_mappings=mappings,
            preview_rows=preview_rows,
            committed=False,
            warnings=warnings,
        )

    summary = commit_uploaded_records(db, normalized_df)
    return UploadResult(
        filename=safe_name,
        row_count=len(df),
        valid_row_count=valid_rows,
        missing_required=missing_req,
        column_mappings=mappings,
        preview_rows=preview_rows,
        committed=True,
        students_upserted=summary.students_upserted,
        records_upserted=summary.records_upserted,
        snapshots_recomputed=summary.snapshots_recomputed,
        warnings=[*warnings, *summary.extra_warnings],
    )
