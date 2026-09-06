import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.schemas.errors import ErrorResponse
from app.security.authentication import create_access_token
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["Authentication"])

class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: str
    role: str

@router.post("/token", response_model=Token, responses={401: {"model": ErrorResponse}})
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Mock login endpoint to obtain a JWT token."""
    # In a real app, verify against the database
    # For simulation, admin gets 'admin' role, others get 'analyst'
    role = "admin" if form_data.username == "admin" else "analyst"
    
    # Check mock password
    if form_data.password != "secret":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    user_id = uuid.uuid4()
    access_token = create_access_token(user_id=user_id, role=role)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": str(user_id),
        "role": role
    }
