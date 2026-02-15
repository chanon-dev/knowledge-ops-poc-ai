import logging
from uuid import UUID, uuid4

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

logger = logging.getLogger(__name__)

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

    if approval.status not in ("pending", "auto_approved"):
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

    # Store verified Q&A pair in Qdrant for future retrieval
    if message:
        try:
            # Find the user's original question
            user_msg_stmt = select(Message).where(
                Message.conversation_id == message.conversation_id,
                Message.role == "user",
                Message.id < message.id,
            ).order_by(Message.id.desc()).limit(1)
            user_msg_result = await db.execute(user_msg_stmt)
            user_message = user_msg_result.scalar_one_or_none()

            if user_message:
                from app.services.rag.embeddings import EmbeddingService
                from app.services.rag.vector_store import VectorStore

                embedder = EmbeddingService()
                vector_store = VectorStore()

                question_text = user_message.content
                answer_text = approval.approved_answer or approval.original_answer

                question_vector = embedder.embed_text(question_text)
                verified_doc_id = f"verified_{approval.id}"

                vector_store.upsert_vectors([{
                    "id": str(uuid4()),
                    "vector": question_vector,
                    "tenant_id": str(approval.tenant_id),
                    "department_id": str(approval.department_id),
                    "document_id": verified_doc_id,
                    "chunk_index": 0,
                    "content": f"Q: {question_text}\nA: {answer_text}",
                    "title": f"Verified: {question_text[:80]}",
                    "source_type": "verified_answer",
                }])
                logger.info(f"Stored verified answer in Qdrant: {verified_doc_id}")
        except Exception as e:
            logger.warning(f"Failed to store verified answer in Qdrant: {e}")

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

    if approval.status not in ("pending", "auto_approved", "approved"):
        raise BadRequestError(f"Approval is already {approval.status}")

    was_approved = approval.status == "approved"

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

    # Remove verified answer from Qdrant if it was previously approved
    if was_approved:
        try:
            from app.services.rag.vector_store import VectorStore
            vector_store = VectorStore()
            verified_doc_id = f"verified_{approval.id}"
            vector_store.delete_by_document(verified_doc_id)
            logger.info(f"Removed verified answer from Qdrant: {verified_doc_id}")
        except Exception as e:
            logger.warning(f"Failed to remove verified answer from Qdrant: {e}")

    return approval
