"""Training catalog CRUD endpoints.

Manages training methods, base model catalog, deployment targets,
and training job history — all stored in the database.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_role
from app.models.training_method import TrainingMethod
from app.models.base_model_catalog import BaseModelCatalog
from app.models.deployment_target import DeploymentTarget
from app.models.training_job import TrainingJob
from app.models.user import User

router = APIRouter()


# -----------------------------------------------------------------------
# Schemas
# -----------------------------------------------------------------------

class TrainingMethodCreate(BaseModel):
    name: str
    method_key: str
    description: str | None = None
    default_config: dict = {}


class TrainingMethodUpdate(BaseModel):
    name: str | None = None
    method_key: str | None = None
    description: str | None = None
    default_config: dict | None = None
    is_active: bool | None = None


class BaseModelCreate(BaseModel):
    model_name: str
    display_name: str
    size_billion: float | None = None
    recommended_ram_gb: float | None = None
    default_target_modules: list[str] | None = None


class BaseModelUpdate(BaseModel):
    display_name: str | None = None
    size_billion: float | None = None
    recommended_ram_gb: float | None = None
    default_target_modules: list[str] | None = None
    is_active: bool | None = None


class DeploymentTargetCreate(BaseModel):
    name: str
    target_key: str
    config: dict = {}


class DeploymentTargetUpdate(BaseModel):
    name: str | None = None
    target_key: str | None = None
    config: dict | None = None
    is_active: bool | None = None


# -----------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------

def _serialize_method(m: TrainingMethod) -> dict:
    return {
        "id": str(m.id),
        "name": m.name,
        "method_key": m.method_key,
        "description": m.description,
        "default_config": m.default_config,
        "is_active": m.is_active,
        "created_at": str(m.created_at),
    }


def _serialize_base_model(m: BaseModelCatalog) -> dict:
    return {
        "id": str(m.id),
        "model_name": m.model_name,
        "display_name": m.display_name,
        "size_billion": m.size_billion,
        "recommended_ram_gb": m.recommended_ram_gb,
        "default_target_modules": m.default_target_modules,
        "is_active": m.is_active,
        "created_at": str(m.created_at),
    }


def _serialize_target(t: DeploymentTarget) -> dict:
    return {
        "id": str(t.id),
        "name": t.name,
        "target_key": t.target_key,
        "config": t.config,
        "is_active": t.is_active,
        "created_at": str(t.created_at),
    }


def _serialize_job(j: TrainingJob) -> dict:
    return {
        "id": str(j.id),
        "base_model_name": j.base_model_name,
        "method_key": j.method_key,
        "config": j.config,
        "status": j.status,
        "progress": j.progress,
        "status_message": j.status_message,
        "error": j.error,
        "metrics": j.metrics,
        "model_name": j.model_name,
        "device_info": j.device_info,
        "deployed_to_target": j.deployed_to_target,
        "started_at": str(j.started_at) if j.started_at else None,
        "completed_at": str(j.completed_at) if j.completed_at else None,
        "created_at": str(j.created_at),
    }


# -----------------------------------------------------------------------
# Training Methods CRUD
# -----------------------------------------------------------------------

@router.get("/methods")
async def list_methods(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    result = await db.execute(
        select(TrainingMethod)
        .where(TrainingMethod.tenant_id == user.tenant_id)
        .order_by(TrainingMethod.created_at.asc())
    )
    return {"data": [_serialize_method(m) for m in result.scalars().all()]}


@router.post("/methods")
async def create_method(
    body: TrainingMethodCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    existing = await db.execute(
        select(TrainingMethod).where(
            TrainingMethod.tenant_id == user.tenant_id,
            TrainingMethod.name == body.name,
        )
    )
    method = existing.scalar_one_or_none()
    if method:
        # Upsert: update existing record instead of 409
        method.method_key = body.method_key
        method.description = body.description
        method.default_config = body.default_config
    else:
        method = TrainingMethod(
            tenant_id=user.tenant_id,
            name=body.name,
            method_key=body.method_key,
            description=body.description,
            default_config=body.default_config,
        )
        db.add(method)
    await db.flush()
    await db.refresh(method)
    return _serialize_method(method)


@router.put("/methods/{method_id}")
async def update_method(
    method_id: UUID,
    body: TrainingMethodUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    result = await db.execute(
        select(TrainingMethod).where(
            TrainingMethod.id == method_id,
            TrainingMethod.tenant_id == user.tenant_id,
        )
    )
    method = result.scalar_one_or_none()
    if not method:
        raise HTTPException(status_code=404, detail="Training method not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(method, field, value)
    await db.flush()
    await db.refresh(method)
    return _serialize_method(method)


@router.delete("/methods/{method_id}")
async def delete_method(
    method_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    result = await db.execute(
        select(TrainingMethod).where(
            TrainingMethod.id == method_id,
            TrainingMethod.tenant_id == user.tenant_id,
        )
    )
    method = result.scalar_one_or_none()
    if not method:
        raise HTTPException(status_code=404, detail="Training method not found")
    await db.delete(method)
    await db.flush()
    return {"ok": True}


# -----------------------------------------------------------------------
# Base Model Catalog CRUD
# -----------------------------------------------------------------------

@router.get("/base-models")
async def list_base_models(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    result = await db.execute(
        select(BaseModelCatalog)
        .where(BaseModelCatalog.tenant_id == user.tenant_id)
        .order_by(BaseModelCatalog.created_at.asc())
    )
    return {"data": [_serialize_base_model(m) for m in result.scalars().all()]}


@router.post("/base-models")
async def create_base_model(
    body: BaseModelCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    existing = await db.execute(
        select(BaseModelCatalog).where(
            BaseModelCatalog.tenant_id == user.tenant_id,
            BaseModelCatalog.model_name == body.model_name,
        )
    )
    model = existing.scalar_one_or_none()
    if model:
        # Upsert: update existing record instead of 409
        model.display_name = body.display_name
        model.size_billion = body.size_billion
        model.recommended_ram_gb = body.recommended_ram_gb
        model.default_target_modules = body.default_target_modules
    else:
        model = BaseModelCatalog(
            tenant_id=user.tenant_id,
            model_name=body.model_name,
            display_name=body.display_name,
            size_billion=body.size_billion,
            recommended_ram_gb=body.recommended_ram_gb,
            default_target_modules=body.default_target_modules,
        )
        db.add(model)
    await db.flush()
    await db.refresh(model)
    return _serialize_base_model(model)


@router.put("/base-models/{model_id}")
async def update_base_model(
    model_id: UUID,
    body: BaseModelUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    result = await db.execute(
        select(BaseModelCatalog).where(
            BaseModelCatalog.id == model_id,
            BaseModelCatalog.tenant_id == user.tenant_id,
        )
    )
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=404, detail="Base model not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(model, field, value)
    await db.flush()
    await db.refresh(model)
    return _serialize_base_model(model)


@router.delete("/base-models/{model_id}")
async def delete_base_model(
    model_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    result = await db.execute(
        select(BaseModelCatalog).where(
            BaseModelCatalog.id == model_id,
            BaseModelCatalog.tenant_id == user.tenant_id,
        )
    )
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=404, detail="Base model not found")
    await db.delete(model)
    await db.flush()
    return {"ok": True}


# -----------------------------------------------------------------------
# Deployment Targets CRUD
# -----------------------------------------------------------------------

@router.get("/targets")
async def list_targets(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    result = await db.execute(
        select(DeploymentTarget)
        .where(DeploymentTarget.tenant_id == user.tenant_id)
        .order_by(DeploymentTarget.created_at.asc())
    )
    return {"data": [_serialize_target(t) for t in result.scalars().all()]}


@router.post("/targets")
async def create_target(
    body: DeploymentTargetCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    existing = await db.execute(
        select(DeploymentTarget).where(
            DeploymentTarget.tenant_id == user.tenant_id,
            DeploymentTarget.name == body.name,
        )
    )
    target = existing.scalar_one_or_none()
    if target:
        # Upsert: update existing record instead of 409
        target.target_key = body.target_key
        target.config = body.config
    else:
        target = DeploymentTarget(
            tenant_id=user.tenant_id,
            name=body.name,
            target_key=body.target_key,
            config=body.config,
        )
        db.add(target)
    await db.flush()
    await db.refresh(target)
    return _serialize_target(target)


@router.put("/targets/{target_id}")
async def update_target(
    target_id: UUID,
    body: DeploymentTargetUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    result = await db.execute(
        select(DeploymentTarget).where(
            DeploymentTarget.id == target_id,
            DeploymentTarget.tenant_id == user.tenant_id,
        )
    )
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="Deployment target not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(target, field, value)
    await db.flush()
    await db.refresh(target)
    return _serialize_target(target)


@router.delete("/targets/{target_id}")
async def delete_target(
    target_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    result = await db.execute(
        select(DeploymentTarget).where(
            DeploymentTarget.id == target_id,
            DeploymentTarget.tenant_id == user.tenant_id,
        )
    )
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="Deployment target not found")
    await db.delete(target)
    await db.flush()
    return {"ok": True}


# -----------------------------------------------------------------------
# Training Jobs (read-only from this endpoint; creation via /models/train)
# -----------------------------------------------------------------------

@router.get("/jobs")
async def list_jobs(
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    query = (
        select(TrainingJob)
        .where(TrainingJob.tenant_id == user.tenant_id)
        .order_by(TrainingJob.created_at.desc())
    )
    if status:
        query = query.where(TrainingJob.status == status)
    result = await db.execute(query)
    return {"data": [_serialize_job(j) for j in result.scalars().all()]}


@router.get("/jobs/{job_id}")
async def get_job(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("member")),
):
    result = await db.execute(
        select(TrainingJob).where(
            TrainingJob.id == job_id,
            TrainingJob.tenant_id == user.tenant_id,
        )
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Training job not found")
    return _serialize_job(job)


# -----------------------------------------------------------------------
# Registry info (what trainers/deployers are available in Python)
# -----------------------------------------------------------------------

@router.get("/registry")
async def get_registry(
    user: User = Depends(require_role("admin")),
):
    """Return registered trainer and deployer implementations."""
    from ml.training.registry import list_trainers, list_deployers
    return {
        "trainers": list_trainers(),
        "deployers": list_deployers(),
    }
