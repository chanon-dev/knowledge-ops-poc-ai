from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_role
from app.models.user import User
from app.services.analytics_service import AnalyticsService

router = APIRouter()


@router.get("/usage")
async def get_usage(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    service = AnalyticsService(db)
    return await service.get_usage_overview(user.tenant_id, date_from, date_to)


@router.get("/departments/{department_id}")
async def get_department_analytics(
    department_id: UUID,
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service = AnalyticsService(db)
    return await service.get_department_stats(user.tenant_id, department_id, date_from, date_to)


@router.get("/ai-performance")
async def get_ai_performance(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    service = AnalyticsService(db)
    return await service.get_ai_performance(user.tenant_id, date_from, date_to)


@router.get("/top-topics")
async def get_top_topics(
    department_id: UUID | None = Query(None),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    service = AnalyticsService(db)
    return await service.get_top_topics(user.tenant_id, department_id, limit)


@router.get("/team-productivity")
async def get_team_productivity(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    service = AnalyticsService(db)
    return await service.get_team_productivity(user.tenant_id)


@router.get("/export")
async def export_analytics(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    service = AnalyticsService(db)
    data = await service.export_analytics(user.tenant_id, date_from, date_to)
    return JSONResponse(content=data)
