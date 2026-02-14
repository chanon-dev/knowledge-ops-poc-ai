from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ApprovalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    department_id: UUID
    message_id: int
    requested_by: UUID | None = None
    reviewed_by: UUID | None = None
    status: str
    original_answer: str
    approved_answer: str | None = None
    rejection_reason: str | None = None
    reviewer_notes: str | None = None
    priority: str
    expires_at: datetime | None = None
    reviewed_at: datetime | None = None
    created_at: datetime


class ApproveAction(BaseModel):
    approved_answer: str | None = None
    reviewer_notes: str | None = None


class RejectAction(BaseModel):
    rejection_reason: str = Field(..., min_length=1)
    corrected_answer: str | None = None
    reviewer_notes: str | None = None
