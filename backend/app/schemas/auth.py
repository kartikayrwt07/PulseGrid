from typing import Literal

from pydantic import BaseModel, Field


class DemoTokenRequest(BaseModel):
    role: Literal["faculty", "student"] = "faculty"
    student_id: int | None = Field(default=None, ge=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: Literal["faculty", "student"]
    student_id: int | None = None
