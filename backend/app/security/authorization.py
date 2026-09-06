from typing import List
from fastapi import Depends, HTTPException, status
from app.security.authentication import get_current_user


def require_role(allowed_roles: List[str]):
    """Enforces role-based access control.
    
    # TODO(M5): Implement fine-grained ABAC (Attribute-Based Access Control) and tenant isolation.
    """
    async def role_checker(current_user: dict = Depends(get_current_user)) -> dict:
        user_role = current_user.get("role", "guest")
        if user_role not in allowed_roles and "admin" not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User role '{user_role}' lacks required permissions (requires one of {allowed_roles})",
            )
        return current_user

    return role_checker
