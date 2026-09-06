import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class SessionCreateRequest(BaseModel):
    user_id: uuid.UUID = Field(..., description="ID of the user initiating the session")
    mode: str = Field(default="realtime", description="Session mode: realtime, batch, or test")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Custom session metadata")


class SessionResponse(BaseModel):
    session_id: uuid.UUID
    user_id: uuid.UUID
    start_time: datetime
    end_time: Optional[datetime] = None
    mode: str
    status: str

    model_config = {"from_attributes": True}


class SessionCloseRequest(BaseModel):
    status: str = Field(default="completed", description="Final session status (e.g. completed, terminated)")
