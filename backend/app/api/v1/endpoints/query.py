from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.query import QueryRequest, QueryResponse
from app.services.query_service import QueryService

router = APIRouter()


@router.post("", response_model=QueryResponse)
async def execute_query(
    body: QueryRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service = QueryService(db)
    result = await service.execute_query(
        tenant_id=user.tenant_id,
        department_id=body.department_id,
        user_id=user.id,
        query_text=body.text,
        conversation_id=body.conversation_id,
        model_name=body.model_name,
    )
    return QueryResponse(**result)
