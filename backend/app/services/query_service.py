from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.graph import QueryState, create_query_graph
from app.core.config import settings
from app.core.exceptions import NotFoundError
from app.models.approval import Approval
from app.models.conversation import Conversation, Message
from app.models.department import Department


class QueryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def execute_query(
        self,
        tenant_id: UUID,
        department_id: UUID,
        user_id: UUID,
        query_text: str,
        conversation_id: UUID | None = None,
        image_path: str | None = None,
    ) -> dict:
        # Get department config
        stmt = select(Department).where(
            Department.id == department_id,
            Department.deleted_at.is_(None),
        )
        result = await self.db.execute(stmt)
        department = result.scalar_one_or_none()
        if not department:
            raise NotFoundError(f"Department {department_id} not found")

        # Get or create conversation
        if conversation_id:
            conv_stmt = select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.tenant_id == tenant_id,
            )
            conv_result = await self.db.execute(conv_stmt)
            conversation = conv_result.scalar_one_or_none()
            if not conversation:
                raise NotFoundError(f"Conversation {conversation_id} not found")
        else:
            conversation = Conversation(
                tenant_id=tenant_id,
                department_id=department_id,
                user_id=user_id,
                title=query_text[:100],
                status="active",
            )
            self.db.add(conversation)
            await self.db.flush()

        # Save user message
        user_msg = Message(
            conversation_id=conversation.id,
            tenant_id=tenant_id,
            department_id=department_id,
            user_id=user_id,
            role="user",
            content=query_text,
            image_path=image_path,
            status="completed",
        )
        self.db.add(user_msg)
        await self.db.flush()

        # Run LangGraph orchestrator
        initial_state: QueryState = {
            "query": query_text,
            "department_id": str(department_id),
            "tenant_id": str(tenant_id),
            "user_id": str(user_id),
            "image_path": image_path,
            "department_config": department.config or {},
            "model_name": settings.OLLAMA_MODEL,
            "confidence_threshold": department.config.get("confidence_threshold", 0.85) if department.config else 0.85,
            "system_prompt": department.config.get("system_prompt", "") if department.config else "",
            "rag_results": [],
            "context": "",
            "answer": "",
            "confidence": 0.0,
            "sources": [],
            "model_used": "",
            "tokens_input": 0,
            "tokens_output": 0,
            "latency_ms": 0.0,
            "needs_approval": False,
            "error": None,
        }

        try:
            graph = create_query_graph()
            final_state = graph.invoke(initial_state)
        except Exception as e:
            final_state = {
                **initial_state,
                "answer": f"I apologize, but I encountered an error: {e}",
                "confidence": 0.0,
                "needs_approval": False,
                "error": str(e),
            }

        # Save AI message
        status = "pending_approval" if final_state.get("needs_approval") else "completed"
        ai_msg = Message(
            conversation_id=conversation.id,
            tenant_id=tenant_id,
            department_id=department_id,
            role="assistant",
            content=final_state.get("answer", ""),
            confidence=final_state.get("confidence", 0.0),
            model_used=final_state.get("model_used"),
            tokens_input=final_state.get("tokens_input", 0),
            tokens_output=final_state.get("tokens_output", 0),
            latency_ms=final_state.get("latency_ms", 0.0),
            sources={"items": final_state.get("sources", [])},
            status=status,
        )
        self.db.add(ai_msg)
        await self.db.flush()

        # Update conversation
        conversation.message_count = (conversation.message_count or 0) + 2
        from sqlalchemy import func
        conversation.last_message_at = func.now()
        await self.db.flush()

        # Create approval if needed
        if final_state.get("needs_approval"):
            approval = Approval(
                tenant_id=tenant_id,
                department_id=department_id,
                message_id=ai_msg.id,
                requested_by=user_id,
                status="pending",
                original_answer=final_state.get("answer", ""),
                priority="normal",
            )
            self.db.add(approval)
            await self.db.flush()

        return {
            "answer": final_state.get("answer", ""),
            "sources": final_state.get("sources", []),
            "confidence": final_state.get("confidence", 0.0),
            "model_used": final_state.get("model_used"),
            "tokens_input": final_state.get("tokens_input", 0),
            "tokens_output": final_state.get("tokens_output", 0),
            "latency_ms": final_state.get("latency_ms", 0.0),
            "conversation_id": conversation.id,
            "message_id": ai_msg.id,
            "needs_approval": final_state.get("needs_approval", False),
        }

    async def get_conversation_history(
        self,
        conversation_id: UUID,
        limit: int = 50,
    ) -> list[Message]:
        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
