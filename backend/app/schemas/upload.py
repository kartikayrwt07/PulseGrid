"""Pydantic schemas for CSV/XLSX ingestion, transactional commit, and demo reset."""

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class ColumnMappingEntry(BaseModel):
    source_column: str
    canonical_column: str | None = None
    confidence: float = Field(..., ge=0.0, le=1.0)
    status: str


class UploadedRecordRow(BaseModel):
    roll_no: str = Field(..., min_length=1, max_length=20)
    student_name: str = Field(..., min_length=1, max_length=120)
    subject_code: str = Field(..., min_length=1, max_length=20)
    week: int = Field(..., ge=1, le=20)
    attended_sessions: int = Field(..., ge=0)
    total_sessions: int = Field(..., ge=1)
    assignment_score: float = Field(..., ge=0.0, le=100.0)
    internal_score: float = Field(..., ge=0.0, le=100.0)

    @model_validator(mode="after")
    def validate_session_bounds(self) -> UploadedRecordRow:
        if self.attended_sessions > self.total_sessions:
            raise ValueError("attended_sessions cannot exceed total_sessions")
        return self


class UploadResult(BaseModel):
    filename: str
    row_count: int
    valid_row_count: int
    missing_required: list[str] = Field(default_factory=list)
    column_mappings: list[ColumnMappingEntry]
    preview_rows: list[dict[str, str | int | float | None]]
    committed: bool = False
    students_upserted: int = 0
    records_upserted: int = 0
    snapshots_recomputed: int = 0
    warnings: list[str] = Field(default_factory=list)


class DemoResetResponse(BaseModel):
    status: str
    students_seeded: int
    snapshots_recomputed: int
