from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.auth import TokenPayload, decode_access_token

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> TokenPayload:
    """Validate Bearer JWT and return authenticated user claims."""
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials required.",
        )
    return decode_access_token(credentials.credentials)


def require_faculty(user: TokenPayload = Depends(get_current_user)) -> TokenPayload:
    """Enforce faculty-only access on cohort/admin endpoints."""
    if user.role != "faculty":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Faculty role required for this resource.",
        )
    return user


def assert_student_scope(user: TokenPayload, target_student_id: int) -> None:
    """Ensure students can access only their own record while faculty can view all."""
    if user.role == "faculty":
        return
    if user.role == "student" and user.student_id == target_student_id:
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access denied: you may only view your own academic analytics.",
    )
