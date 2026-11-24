from datetime import UTC, datetime, timedelta
from typing import Any, Literal

import jwt
from fastapi import HTTPException, status
from pydantic import BaseModel

from app.core.config import get_settings

RoleType = Literal["faculty", "student"]


class TokenPayload(BaseModel):
    sub: str
    role: RoleType
    student_id: int | None = None
    exp: int


def create_access_token(
    subject: str,
    role: RoleType,
    student_id: int | None = None,
    expires_minutes: int | None = None,
) -> str:
    """Create a signed JWT token using SECRET_KEY from environment."""
    settings = get_settings()
    ttl = expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES
    expire_at = datetime.now(UTC) + timedelta(minutes=ttl)
    payload: dict[str, Any] = {
        "sub": subject,
        "role": role,
        "student_id": student_id,
        "exp": int(expire_at.timestamp()),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> TokenPayload:
    """Verify and decode a JWT token; raises 401 on invalid/expired tokens."""
    settings = get_settings()
    try:
        raw = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return TokenPayload.model_validate(raw)
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session token expired. Please re-authenticate.",
        ) from exc
    except (jwt.InvalidTokenError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
        ) from exc
