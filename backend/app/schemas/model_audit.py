"""Pydantic schemas for holdout model evaluation audit."""

from __future__ import annotations

from pydantic import BaseModel, Field


class CalibrationBin(BaseModel):
    bin_mean_pred: float
    bin_true_freq: float
    bin_count: int


class ModelComparisonEntry(BaseModel):
    model_name: str
    at_risk_recall: float
    macro_f1: float
    roc_auc: float
    confusion_matrix: list[list[int]]
    cv_at_risk_recall_mean: float = 0.0
    cv_at_risk_recall_std: float = 0.0
    cv_macro_f1_mean: float = 0.0
    cv_macro_f1_std: float = 0.0
    cv_roc_auc_mean: float = 0.0


class FeatureImportanceEntry(BaseModel):
    feature: str
    label: str
    importance: float


class ModelAuditResponse(BaseModel):
    selected_model: str
    feature_window_weeks: str
    target_window_weeks: str
    train_size: int
    holdout_size: int
    class_labels: list[str]
    at_risk_recall: float
    macro_f1: float
    roc_auc: float
    mae: float
    brier_score: float = 0.0
    calibration_curve: list[CalibrationBin] = Field(default_factory=list)
    confusion_matrix: list[list[int]]
    model_comparison: list[ModelComparisonEntry]
    feature_importances: list[FeatureImportanceEntry]
