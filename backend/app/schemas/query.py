from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)
    department_id: UUID
    conversation_id: UUID | None = None


class SourceItem(BaseModel):
    title: str
    chunk: str
    score: float
    document_id: str | None = None


class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceItem] = []
    confidence: float
    model_used: str | None = None
    tokens_input: int = 0
    tokens_output: int = 0
    latency_ms: float = 0
    conversation_id: UUID
    message_id: int
    needs_approval: bool = False
