from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    db_ok: bool
    model_loaded: bool
    dataset_count: int
    active_week: int = 9
    total_weeks: int = 14
