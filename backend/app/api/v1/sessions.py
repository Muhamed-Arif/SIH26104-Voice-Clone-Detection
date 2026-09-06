import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.connection import get_db
from app.schemas.session import SessionCreateRequest, SessionResponse
from app.schemas.errors import ErrorResponse
from app.services.session_manager import SessionManager
from app.security.authentication import get_current_user

router = APIRouter(prefix="/sessions", tags=["Sessions"])


@router.post(
    "",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new voice analysis session",
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def create_session(
    payload: SessionCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> SessionResponse:
    """Initializes a new real-time or batch voice analysis session."""
    manager = SessionManager(db)
    session = await manager.create_session(
        user_id=payload.user_id,
        mode=payload.mode,
    )
    return SessionResponse.model_validate(session)


@router.get(
    "/{session_id}",
    response_model=SessionResponse,
    summary="Get session details by ID",
    responses={404: {"model": ErrorResponse}},
)
async def get_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> SessionResponse:
    """Retrieves session metadata and current status."""
    manager = SessionManager(db)
    session = await manager.get_session(session_id)
    return SessionResponse.model_validate(session)
