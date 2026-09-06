import uuid
from typing import Optional
from pydantic import BaseModel, Field


class VerificationRequest(BaseModel):
    analysis_id: uuid.UUID = Field(..., description="UUID of the analysis event to verify or override")
    verifier_id: Optional[uuid.UUID] = Field(None, description="UUID of the verifying user/analyst")
    decision: str = Field(..., description="Verification decision: CONFIRMED_SPOOF, FALSE_POSITIVE, BENIGN, REJECT")
    notes: Optional[str] = Field(None, description="Detailed notes on the manual verification")


class VerificationResponse(BaseModel):
    status: str = Field(..., description="Status of the verification action")
    analysis_id: uuid.UUID
    decision: str
    verified_at: str
    audit_id: uuid.UUID
