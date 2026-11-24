from fastapi import APIRouter, HTTPException, Query, status

from app.core.auth import RoleType, create_access_token
from app.core.config import get_settings
from app.schemas.auth import DemoTokenRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/demo-token", response_model=TokenResponse)
def issue_demo_token(
    body: DemoTokenRequest | None = None,
    role: RoleType | None = Query(default=None),
    student_id: int | None = Query(default=None, ge=1),
) -> TokenResponse:
    """Issue a signed demo JWT when DEMO_MODE is explicitly enabled."""
    settings = get_settings()
    if not settings.DEMO_MODE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Demo token endpoint is disabled outside DEMO_MODE.",
        )

    chosen_role: RoleType = role or (body.role if body else "faculty")
    chosen_student_id = (
        student_id if student_id is not None else (body.student_id if body else None)
    )

    if chosen_role == "student" and chosen_student_id is None:
        chosen_student_id = 1

    subject = f"student:{chosen_student_id}" if chosen_role == "student" else "faculty:FAC-001"
    token = create_access_token(
        subject=subject,
        role=chosen_role,
        student_id=chosen_student_id if chosen_role == "student" else None,
    )
    return TokenResponse(
        access_token=token,
        role=chosen_role,
        student_id=chosen_student_id if chosen_role == "student" else None,
    )
