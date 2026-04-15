"""
JWT authentication middleware.
Validates Supabase-issued JWTs on protected routes.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from app.config import get_settings

bearer_scheme = HTTPBearer()


def require_auth(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    """
    Dependency: validates Supabase JWT and returns decoded payload.
    Usage: user = Depends(require_auth)
    """
    settings = get_settings()
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            options={"verify_aud": False},
        )
        return payload
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def get_user_id(payload: dict = Depends(require_auth)) -> str:
    """Extract user UUID from JWT payload."""
    uid = payload.get("sub")
    if not uid:
        raise HTTPException(status_code=401, detail="Missing user ID in token")
    return uid
