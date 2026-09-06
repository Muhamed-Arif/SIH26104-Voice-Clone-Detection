from typing import Callable, Coroutine, Any
from fastapi import Depends, HTTPException, status
from app.security.authentication import get_current_user
from app.core.logging import get_logger

logger = get_logger(__name__)

def require_role(required_role: str) -> Callable[[dict], Coroutine[Any, Any, dict]]:
    """Dependency that checks if the current user has the required role."""
    async def role_checker(current_user: dict = Depends(get_current_user)) -> dict:
        user_role = current_user.get("role", "analyst")
        if user_role != required_role and user_role != "admin":
            logger.warning(f"Access denied: User {current_user.get('user_id')} needs {required_role}, has {user_role}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation requires {required_role} role.",
            )
        return current_user
    return role_checker

async def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """Convenience dependency for admin-only routes."""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation requires admin role.",
        )
    return current_user
