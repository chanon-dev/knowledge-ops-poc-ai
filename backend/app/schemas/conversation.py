from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    conversation_id: UUID
    role: str
    content: str
    image_path: str | None = None
    confidence: float | None = None
    model_used: str | None = None
    tokens_input: int | None = None
    tokens_output: int | None = None
    latency_ms: float | None = None
    sources: dict | None = None
    status: str
    approval_id: UUID | None = None
    created_at: datetime


class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    department_id: UUID
    user_id: UUID
    title: str | None = None
    status: str
    message_count: int
    last_message_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class ConversationWithMessages(ConversationResponse):
    messages: list[MessageResponse] = []
