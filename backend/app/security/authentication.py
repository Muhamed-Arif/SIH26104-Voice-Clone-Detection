import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from app.core.config import settings
from app.core.exceptions import AuthenticationException
from app.database.base import User

# Optional bearer scheme for routes
security_scheme = HTTPBearer(auto_error=False)


def create_access_token(user_id: uuid.UUID, role: str = "analyst", expires_delta: Optional[timedelta] = None) -> str:
    """Creates a signed JWT access token.
    
    # TODO(M5): Add asymmetric RSA signing keys or integrating with corporate IdP/OAuth2 provider.
    """
    to_encode = {"sub": str(user_id), "role": role}
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
) -> Optional[dict]:
    """Extracts claims from token if present, returns None if not supplied (for open endpoints).
    
    # TODO(M5): Add token revocation check via Redis blacklist.
    """
    if not credentials:
        return None
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            return None
        return {"user_id": uuid.UUID(user_id_str), "role": payload.get("role", "analyst")}
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
) -> dict:
    """Requires a valid JWT token.
    
    # TODO(M5): Connect directly to identity directory / LDAP.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = await get_current_user_optional(credentials)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
