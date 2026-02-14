from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_role
from app.core.exceptions import BadRequestError, NotFoundError
from app.models.approval import Approval
from app.models.conversation import Message
from app.models.user import User
from app.schemas.approval import ApprovalResponse, ApproveAction, RejectAction
from app.schemas.common import PaginatedResponse, PaginationParams, build_paginated_response

router = APIRouter()


@router.get("", response_model=PaginatedResponse[ApprovalResponse])
async def list_approvals(
    department_id: UUID | None = None,
    status: str = "pending",
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    base = select(Approval).where(
        Approval.tenant_id == user.tenant_id,
        Approval.status == status,
    )
    if department_id:
        base = base.where(Approval.department_id == department_id)

    count_stmt = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = (
        base.order_by(Approval.created_at.desc())
        .offset(pagination.offset)
        .limit(pagination.per_page)
    )
    result = await db.execute(stmt)
    items = list(result.scalars().all())
    return build_paginated_response(items, total, pagination, ApprovalResponse)


@router.get("/{approval_id}", response_model=ApprovalResponse)
async def get_approval(
    approval_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(Approval).where(
        Approval.id == approval_id,
        Approval.tenant_id == user.tenant_id,
    )
    result = await db.execute(stmt)
    approval = result.scalar_one_or_none()
    if not approval:
        raise NotFoundError("Approval not found")
    return approval


@router.post("/{approval_id}/approve", response_model=ApprovalResponse)
async def approve(
    approval_id: UUID,
    body: ApproveAction,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("member")),
):
    stmt = select(Approval).where(
        Approval.id == approval_id,
        Approval.tenant_id == user.tenant_id,
    )
    result = await db.execute(stmt)
    approval = result.scalar_one_or_none()
    if not approval:
        raise NotFoundError("Approval not found")

    if approval.status != "pending":
        raise BadRequestError(f"Approval is already {approval.status}")

    approval.status = "approved"
    approval.reviewed_by = user.id
    approval.approved_answer = body.approved_answer or approval.original_answer
    approval.reviewer_notes = body.reviewer_notes
    approval.reviewed_at = func.now()

    # Update the message status
    msg_stmt = select(Message).where(Message.id == approval.message_id)
    msg_result = await db.execute(msg_stmt)
    message = msg_result.scalar_one_or_none()
    if message:
        message.status = "approved"
        if body.approved_answer:
            message.content = body.approved_answer

    await db.flush()
    await db.refresh(approval)
    return approval


@router.post("/{approval_id}/reject", response_model=ApprovalResponse)
async def reject(
    approval_id: UUID,
    body: RejectAction,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("member")),
):
    stmt = select(Approval).where(
        Approval.id == approval_id,
        Approval.tenant_id == user.tenant_id,
    )
    result = await db.execute(stmt)
    approval = result.scalar_one_or_none()
    if not approval:
        raise NotFoundError("Approval not found")

    if approval.status != "pending":
        raise BadRequestError(f"Approval is already {approval.status}")

    approval.status = "rejected"
    approval.reviewed_by = user.id
    approval.rejection_reason = body.rejection_reason
    approval.reviewer_notes = body.reviewer_notes
    approval.reviewed_at = func.now()

    if body.corrected_answer:
        approval.approved_answer = body.corrected_answer

    # Update the message status
    msg_stmt = select(Message).where(Message.id == approval.message_id)
    msg_result = await db.execute(msg_stmt)
    message = msg_result.scalar_one_or_none()
    if message:
        message.status = "rejected"

    await db.flush()
    await db.refresh(approval)
    return approval
