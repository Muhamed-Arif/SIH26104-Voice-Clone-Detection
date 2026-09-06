from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error explanation")
    field: Optional[str] = Field(None, description="Specific field associated with the error if validation failure")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional error context or debug information")


class ErrorResponse(BaseModel):
    success: bool = Field(default=False, description="Always false for error responses")
    error: ErrorDetail = Field(..., description="Error detail payload")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp of the error")
    request_id: Optional[str] = Field(None, description="Correlation or request trace ID")
