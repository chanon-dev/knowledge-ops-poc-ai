"""Model management API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_role
from app.models.user import User

router = APIRouter()


class TrainRequest(BaseModel):
    department_id: UUID | None = None
    base_model: str = "mistralai/Mistral-7B-v0.1"
    epochs: int = 3
    learning_rate: float = 2e-4


class ModelInfo(BaseModel):
    id: str
    name: str
    base_model: str
    department_id: UUID | None
    status: str  # training, ready, failed, archived
    metrics: dict = {}
    created_at: str


# In-memory training job tracker (in production, use DB or Redis)
_training_jobs: dict[str, dict] = {}


@router.get("")
async def list_models(
    department_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    """List trained models, optionally filtered by department."""
    from app.models.audit_log import AuditLog
    from sqlalchemy import select

    query = select(AuditLog).where(
        AuditLog.tenant_id == user.tenant_id,
        AuditLog.action == "model:registered",
    ).order_by(AuditLog.created_at.desc())

    if department_id:
        # Filter by department in details JSON
        pass

    result = await db.execute(query)
    logs = result.scalars().all()

    models = []
    for log in logs:
        details = log.details or {}
        models.append({
            "id": str(log.id),
            "name": details.get("model_name", "unknown"),
            "base_model": details.get("base_model", ""),
            "department_id": details.get("department_id"),
            "status": details.get("status", "ready"),
            "metrics": details.get("metrics", {}),
            "created_at": str(log.created_at),
        })

    return {"data": models}


@router.post("/train")
async def trigger_training(
    body: TrainRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    """Trigger a model training run."""
    import uuid
    job_id = str(uuid.uuid4())

    _training_jobs[job_id] = {
        "id": job_id,
        "tenant_id": str(user.tenant_id),
        "department_id": str(body.department_id) if body.department_id else None,
        "base_model": body.base_model,
        "status": "queued",
        "progress": 0,
    }

    background_tasks.add_task(_run_training, job_id, body, str(user.tenant_id), db)

    return {"job_id": job_id, "status": "queued"}


@router.get("/{job_id}/status")
async def get_training_status(job_id: str, user: User = Depends(require_role("member"))):
    """Get training job status."""
    job = _training_jobs.get(job_id)
    if not job:
        return {"error": "Job not found"}
    return job


async def _run_training(job_id: str, body: TrainRequest, tenant_id: str, db: AsyncSession):
    """Background task to run model training."""
    import logging
    logger = logging.getLogger(__name__)

    try:
        _training_jobs[job_id]["status"] = "running"
        _training_jobs[job_id]["progress"] = 10

        from ml.training.data_pipeline import TrainingDataPipeline
        from app.core.config import settings

        pipeline = TrainingDataPipeline()
        db_url = str(settings.DATABASE_URL).replace("+asyncpg", "")
        df = pipeline.export_approved_qa_pairs(db_url, tenant_id)

        if len(df) < 10:
            _training_jobs[job_id]["status"] = "failed"
            _training_jobs[job_id]["error"] = "Not enough training data (minimum 10 samples)"
            return

        _training_jobs[job_id]["progress"] = 30
        data = pipeline.convert_to_instruction_format(df)
        data = pipeline.clean_and_deduplicate(data)
        train, val, test = pipeline.split_dataset(data)

        _training_jobs[job_id]["progress"] = 50

        from ml.training.lora_trainer import LoRATrainer
        trainer = LoRATrainer()
        trainer.setup(base_model=body.base_model)

        _training_jobs[job_id]["progress"] = 60
        metrics = trainer.train(train, val, epochs=body.epochs, lr=body.learning_rate)

        _training_jobs[job_id]["progress"] = 80
        eval_metrics = trainer.evaluate(test)
        metrics.update(eval_metrics)

        output_dir = f"/tmp/lora_{job_id}"
        trainer.save_adapter(output_dir)

        _training_jobs[job_id]["progress"] = 100
        _training_jobs[job_id]["status"] = "completed"
        _training_jobs[job_id]["metrics"] = metrics

        # Log to audit
        from app.models.audit_log import AuditLog
        from uuid import UUID
        log = AuditLog(
            tenant_id=UUID(tenant_id),
            action="model:registered",
            resource_type="model",
            details={
                "model_name": f"lora-{job_id[:8]}",
                "base_model": body.base_model,
                "department_id": str(body.department_id) if body.department_id else None,
                "status": "ready",
                "metrics": metrics,
            },
        )
        db.add(log)
        await db.commit()

    except Exception as e:
        logger.error(f"Training job {job_id} failed: {e}")
        _training_jobs[job_id]["status"] = "failed"
        _training_jobs[job_id]["error"] = str(e)
