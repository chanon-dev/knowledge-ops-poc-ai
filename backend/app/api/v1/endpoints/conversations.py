from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.exceptions import NotFoundError
from app.models.conversation import Conversation, Message
from app.models.user import User
from app.schemas.common import PaginatedResponse, PaginationParams, build_paginated_response
from app.schemas.conversation import ConversationResponse, ConversationWithMessages, MessageResponse

router = APIRouter()


@router.get("", response_model=PaginatedResponse[ConversationResponse])
async def list_conversations(
    department_id: UUID | None = None,
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    base = select(Conversation).where(
        Conversation.tenant_id == user.tenant_id,
        Conversation.user_id == user.id,
    )
    if department_id:
        base = base.where(Conversation.department_id == department_id)

    count_stmt = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = (
        base.order_by(Conversation.updated_at.desc())
        .offset(pagination.offset)
        .limit(pagination.per_page)
    )
    result = await db.execute(stmt)
    items = list(result.scalars().all())
    return build_paginated_response(items, total, pagination, ConversationResponse)


@router.get("/{conversation_id}", response_model=ConversationWithMessages)
async def get_conversation(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(Conversation).where(
        Conversation.id == conversation_id,
        Conversation.tenant_id == user.tenant_id,
    )
    result = await db.execute(stmt)
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise NotFoundError("Conversation not found")

    msg_stmt = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
        .limit(200)
    )
    msg_result = await db.execute(msg_stmt)
    messages = list(msg_result.scalars().all())

    conv_data = ConversationResponse.model_validate(conversation).model_dump()
    conv_data["messages"] = [MessageResponse.model_validate(m) for m in messages]
    return conv_data


@router.delete("/{conversation_id}", status_code=204)
async def delete_conversation(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(Conversation).where(
        Conversation.id == conversation_id,
        Conversation.tenant_id == user.tenant_id,
        Conversation.user_id == user.id,
    )
    result = await db.execute(stmt)
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise NotFoundError("Conversation not found")

    await db.delete(conversation)
    await db.flush()
