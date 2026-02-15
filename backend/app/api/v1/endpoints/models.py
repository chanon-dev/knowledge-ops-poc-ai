"""Model management API endpoints."""

import os
from uuid import UUID

from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.api.deps import get_current_user, get_db, require_role
from app.models.ai_provider import AIProvider
from app.models.allowed_model import AllowedModel
from app.models.user import User

router = APIRouter()


# --- Schemas ---

class AllowedModelCreate(BaseModel):
    model_name: str
    provider_id: UUID | None = None


class ProviderCreate(BaseModel):
    name: str
    provider_type: str  # "ollama" or "openai_compatible"
    base_url: str
    api_key: str | None = None


# --- Provider endpoints ---

@router.get("/providers")
async def list_providers(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    """List AI providers for this tenant (admin only)."""
    result = await db.execute(
        select(AIProvider)
        .where(AIProvider.tenant_id == user.tenant_id)
        .order_by(AIProvider.created_at.asc())
    )
    providers = result.scalars().all()
    return {
        "data": [
            {
                "id": str(p.id),
                "name": p.name,
                "provider_type": p.provider_type,
                "base_url": p.base_url,
                "has_api_key": bool(p.api_key),
                "is_active": p.is_active,
                "created_at": str(p.created_at),
            }
            for p in providers
        ]
    }


@router.post("/providers")
async def add_provider(
    body: ProviderCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    """Add an AI provider (admin only)."""
    existing = await db.execute(
        select(AIProvider).where(
            AIProvider.tenant_id == user.tenant_id,
            AIProvider.name == body.name,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Provider name already exists")

    provider = AIProvider(
        tenant_id=user.tenant_id,
        name=body.name,
        provider_type=body.provider_type,
        base_url=body.base_url,
        api_key=body.api_key,
    )
    db.add(provider)
    await db.flush()
    await db.refresh(provider)

    return {
        "id": str(provider.id),
        "name": provider.name,
        "provider_type": provider.provider_type,
        "base_url": provider.base_url,
        "has_api_key": bool(provider.api_key),
        "is_active": provider.is_active,
        "created_at": str(provider.created_at),
    }


@router.delete("/providers/{provider_id}")
async def remove_provider(
    provider_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    """Remove an AI provider (admin only)."""
    result = await db.execute(
        select(AIProvider).where(
            AIProvider.id == provider_id,
            AIProvider.tenant_id == user.tenant_id,
        )
    )
    provider = result.scalar_one_or_none()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    await db.delete(provider)
    await db.flush()
    return {"ok": True}


@router.get("/providers/{provider_id}/models")
async def list_provider_models(
    provider_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    """List available models from a specific provider (admin only)."""
    result = await db.execute(
        select(AIProvider).where(
            AIProvider.id == provider_id,
            AIProvider.tenant_id == user.tenant_id,
        )
    )
    provider = result.scalar_one_or_none()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    if provider.provider_type == "ollama":
        from app.services.llm.ollama_client import OllamaClient
        client = OllamaClient(base_url=provider.base_url)
    else:
        from app.services.llm.openai_client import OpenAICompatibleClient
        client = OpenAICompatibleClient(base_url=provider.base_url, api_key=provider.api_key)

    try:
        models = await client.list_models()
        return {"data": models}
    except Exception:
        return {"data": []}
    finally:
        await client.close()


# --- Available / Allowed model endpoints ---

@router.get("/available")
async def list_available_models(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List models available for chat. Uses whitelist if configured, otherwise all Ollama models."""
    result = await db.execute(
        select(AllowedModel)
        .options(joinedload(AllowedModel.provider))
        .where(AllowedModel.tenant_id == user.tenant_id)
        .order_by(AllowedModel.created_at.asc())
    )
    allowed = result.unique().scalars().all()

    if allowed:
        return {
            "data": [
                {
                    "name": m.model_name,
                    "size": 0,
                    "is_default": m.is_default,
                    "provider_name": m.provider.name if m.provider else "Ollama",
                }
                for m in allowed
            ]
        }

    # Fallback: return all Ollama models
    from app.services.llm.ollama_client import OllamaClient
    client = OllamaClient()
    try:
        models = await client.list_models()
        return {
            "data": [
                {"name": m.get("name", ""), "size": m.get("size", 0), "is_default": False, "provider_name": "Ollama"}
                for m in models
            ]
        }
    except Exception:
        return {"data": []}
    finally:
        await client.close()


@router.get("/ollama")
async def list_ollama_models(
    user: User = Depends(require_role("admin")),
):
    """List all models from default Ollama server (admin only)."""
    from app.services.llm.ollama_client import OllamaClient
    client = OllamaClient()
    try:
        models = await client.list_models()
        return {
            "data": [
                {"name": m.get("name", ""), "size": m.get("size", 0)}
                for m in models
            ]
        }
    except Exception:
        return {"data": []}
    finally:
        await client.close()


@router.get("/allowed")
async def list_allowed_models(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    """List allowed models for this tenant (admin only)."""
    result = await db.execute(
        select(AllowedModel)
        .options(joinedload(AllowedModel.provider))
        .where(AllowedModel.tenant_id == user.tenant_id)
        .order_by(AllowedModel.created_at.asc())
    )
    allowed = result.unique().scalars().all()
    return {
        "data": [
            {
                "id": str(m.id),
                "model_name": m.model_name,
                "is_default": m.is_default,
                "provider_id": str(m.provider_id) if m.provider_id else None,
                "provider_name": m.provider.name if m.provider else "Ollama",
                "created_at": str(m.created_at),
            }
            for m in allowed
        ]
    }


@router.post("/allowed")
async def add_allowed_model(
    body: AllowedModelCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    """Add a model to the whitelist (admin only)."""
    existing = await db.execute(
        select(AllowedModel).where(
            AllowedModel.tenant_id == user.tenant_id,
            AllowedModel.model_name == body.model_name,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Model already in whitelist")

    model = AllowedModel(
        tenant_id=user.tenant_id,
        model_name=body.model_name,
        provider_id=body.provider_id,
    )
    db.add(model)
    await db.flush()
    await db.refresh(model)

    return {
        "id": str(model.id),
        "model_name": model.model_name,
        "is_default": model.is_default,
        "provider_id": str(model.provider_id) if model.provider_id else None,
        "created_at": str(model.created_at),
    }


@router.delete("/allowed/{model_id}")
async def remove_allowed_model(
    model_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    """Remove a model from the whitelist (admin only)."""
    result = await db.execute(
        select(AllowedModel).where(
            AllowedModel.id == model_id,
            AllowedModel.tenant_id == user.tenant_id,
        )
    )
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    await db.delete(model)
    await db.flush()
    return {"ok": True}


class TrainRequest(BaseModel):
    method_key: str = "lora"
    base_model_name: str | None = None  # None = use TRAINING_DEFAULT_BASE_MODEL from settings
    deployment_target_key: str | None = None  # None = use default from settings
    method_id: UUID | None = None  # optional catalog reference
    base_model_id: UUID | None = None
    deployment_target_id: UUID | None = None
    config_overrides: dict = {}  # override any training params (epochs, lr, batch_size, etc.)
    force_device: str | None = None  # "cuda", "mps", "cpu", or None for auto


@router.get("")
async def list_models(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    """List completed training jobs as 'trained models'."""
    from app.models.training_job import TrainingJob

    result = await db.execute(
        select(TrainingJob)
        .where(
            TrainingJob.tenant_id == user.tenant_id,
            TrainingJob.status == "completed",
        )
        .order_by(TrainingJob.created_at.desc())
    )
    jobs = result.scalars().all()
    return {
        "data": [
            {
                "id": str(j.id),
                "name": j.model_name or f"lora-{str(j.id)[:8]}",
                "base_model": j.base_model_name,
                "status": "ready",
                "metrics": j.metrics or {},
                "created_at": str(j.created_at),
            }
            for j in jobs
        ]
    }


@router.get("/training-config")
async def get_training_config(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    """Return training defaults, device info, and catalog data for the frontend."""
    from app.core.config import settings
    from app.models.training_method import TrainingMethod
    from app.models.base_model_catalog import BaseModelCatalog
    from app.models.deployment_target import DeploymentTarget

    # Get device info and registry (may fail if torch not installed)
    device = {"device": "unknown"}
    trainers_registry: dict[str, str] = {}
    deployers_registry: dict[str, str] = {}
    try:
        from ml.training.registry import get_trainer, list_trainers, list_deployers
        trainers_registry = list_trainers()
        deployers_registry = list_deployers()
        default_trainer_cls = get_trainer("lora")
        trainer_instance = default_trainer_cls()
        device = trainer_instance.device_info
    except Exception:
        pass

    # Fetch catalogs for this tenant
    methods_result = await db.execute(
        select(TrainingMethod)
        .where(TrainingMethod.tenant_id == user.tenant_id, TrainingMethod.is_active.is_(True))
    )
    models_result = await db.execute(
        select(BaseModelCatalog)
        .where(BaseModelCatalog.tenant_id == user.tenant_id, BaseModelCatalog.is_active.is_(True))
    )
    targets_result = await db.execute(
        select(DeploymentTarget)
        .where(DeploymentTarget.tenant_id == user.tenant_id, DeploymentTarget.is_active.is_(True))
    )

    return {
        "defaults": {
            "base_model": settings.TRAINING_DEFAULT_BASE_MODEL,
            "epochs": settings.TRAINING_DEFAULT_EPOCHS,
            "learning_rate": settings.TRAINING_DEFAULT_LR,
            "batch_size": settings.TRAINING_DEFAULT_BATCH_SIZE,
            "deploy_to_ollama": settings.TRAINING_DEPLOY_TO_OLLAMA,
            "min_samples": settings.TRAINING_MIN_SAMPLES,
        },
        "device": device,
        "registry": {
            "trainers": trainers_registry,
            "deployers": deployers_registry,
        },
        "catalog": {
            "methods": [
                {"id": str(m.id), "name": m.name, "method_key": m.method_key, "default_config": m.default_config}
                for m in methods_result.scalars().all()
            ],
            "base_models": [
                {
                    "id": str(m.id), "model_name": m.model_name, "display_name": m.display_name,
                    "size_billion": m.size_billion, "recommended_ram_gb": m.recommended_ram_gb,
                    "default_target_modules": m.default_target_modules,
                }
                for m in models_result.scalars().all()
            ],
            "targets": [
                {"id": str(t.id), "name": t.name, "target_key": t.target_key, "config": t.config}
                for t in targets_result.scalars().all()
            ],
        },
    }


@router.post("/train")
async def trigger_training(
    body: TrainRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    """Trigger a model training run. Persists job to DB."""
    from app.core.config import settings
    from app.models.training_job import TrainingJob

    # Resolve base model name
    base_model_name = body.base_model_name or settings.TRAINING_DEFAULT_BASE_MODEL

    # Build merged config: settings defaults → catalog defaults → request overrides
    config = {
        "epochs": settings.TRAINING_DEFAULT_EPOCHS,
        "learning_rate": settings.TRAINING_DEFAULT_LR,
        "batch_size": settings.TRAINING_DEFAULT_BATCH_SIZE,
        "force_device": body.force_device,
    }

    # Merge catalog method defaults if method_id provided
    if body.method_id:
        from app.models.training_method import TrainingMethod
        method_result = await db.execute(
            select(TrainingMethod).where(TrainingMethod.id == body.method_id)
        )
        method = method_result.scalar_one_or_none()
        if method and method.default_config:
            config.update(method.default_config)

    # Merge catalog base model defaults if base_model_id provided
    if body.base_model_id:
        from app.models.base_model_catalog import BaseModelCatalog
        bm_result = await db.execute(
            select(BaseModelCatalog).where(BaseModelCatalog.id == body.base_model_id)
        )
        bm = bm_result.scalar_one_or_none()
        if bm:
            base_model_name = bm.model_name
            if bm.default_target_modules:
                config["target_modules"] = bm.default_target_modules

    # Apply request overrides last (highest priority)
    config.update(body.config_overrides)

    # Resolve deployment target key
    deploy_target_key = body.deployment_target_key
    if not deploy_target_key and body.deployment_target_id:
        from app.models.deployment_target import DeploymentTarget
        dt_result = await db.execute(
            select(DeploymentTarget).where(DeploymentTarget.id == body.deployment_target_id)
        )
        dt = dt_result.scalar_one_or_none()
        if dt:
            deploy_target_key = dt.target_key
            config["deploy_config"] = dt.config
    if not deploy_target_key and settings.TRAINING_DEPLOY_TO_OLLAMA:
        deploy_target_key = "ollama"

    config["deploy_target_key"] = deploy_target_key

    # Create DB job
    job = TrainingJob(
        tenant_id=user.tenant_id,
        user_id=user.id,
        method_id=body.method_id,
        base_model_id=body.base_model_id,
        deployment_target_id=body.deployment_target_id,
        base_model_name=base_model_name,
        method_key=body.method_key,
        config=config,
        status="queued",
        progress=0,
    )
    db.add(job)
    await db.flush()
    await db.refresh(job)
    job_id = str(job.id)

    # Commit so background task can read it
    await db.commit()

    background_tasks.add_task(_run_training, job_id)

    return {"job_id": job_id, "status": "queued"}


@router.get("/{job_id}/status")
async def get_training_status(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("member")),
):
    """Get training job status from DB."""
    from app.models.training_job import TrainingJob

    result = await db.execute(
        select(TrainingJob).where(
            TrainingJob.id == job_id,
            TrainingJob.tenant_id == user.tenant_id,
        )
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return {
        "id": str(job.id),
        "status": job.status,
        "progress": job.progress,
        "error": job.error,
        "metrics": job.metrics,
        "model_name": job.model_name,
        "deployed_to_target": job.deployed_to_target,
        "device_info": job.device_info,
        "base_model_name": job.base_model_name,
        "method_key": job.method_key,
    }


async def _run_training(job_id: str):
    """Background task to run model training.

    Reads all config from the TrainingJob DB record.
    Uses the registry to look up trainer and deployer by key.
    """
    import logging
    from datetime import datetime, timezone
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    from app.models.training_job import TrainingJob
    from app.core.config import settings

    logger = logging.getLogger(__name__)

    # Use sync session for background task (not in async request context)
    sync_url = str(settings.DATABASE_URL).replace("+asyncpg", "")
    engine = create_engine(sync_url)

    with Session(engine) as session:
        job = session.get(TrainingJob, job_id)
        if not job:
            logger.error(f"Training job {job_id} not found in DB")
            return

        config = job.config or {}

        try:
            job.status = "running"
            job.progress = 10
            job.started_at = datetime.now(timezone.utc)
            session.commit()

            # 1. Export training data
            from ml.training.data_pipeline import TrainingDataPipeline
            pipeline = TrainingDataPipeline()
            df = pipeline.export_approved_qa_pairs(sync_url, str(job.tenant_id))

            min_samples = settings.TRAINING_MIN_SAMPLES
            if len(df) < min_samples:
                job.status = "failed"
                job.error = f"Not enough training data (found {len(df)}, minimum {min_samples})"
                session.commit()
                return

            # 2. Prepare dataset
            job.progress = 30
            session.commit()

            data = pipeline.convert_to_instruction_format(df)
            data = pipeline.clean_and_deduplicate(data)
            train_data, val_data, test_data = pipeline.split_dataset(data)

            # 3. Setup trainer via registry
            job.progress = 50
            session.commit()

            from ml.training.registry import get_trainer
            TrainerClass = get_trainer(job.method_key)
            trainer = TrainerClass(force_device=config.get("force_device"))
            trainer.setup(
                base_model=job.base_model_name,
                **{k: v for k, v in config.items() if k in ("lora_r", "lora_alpha", "lora_dropout", "target_modules")},
            )
            job.device_info = trainer.device_info

            # 4. Train
            job.progress = 60
            session.commit()

            output_dir = os.path.join(settings.TRAINING_OUTPUT_DIR, job_id)
            metrics = trainer.train(
                train_data, val_data,
                output_dir=output_dir,
                epochs=config.get("epochs", settings.TRAINING_DEFAULT_EPOCHS),
                lr=config.get("learning_rate", settings.TRAINING_DEFAULT_LR),
                batch_size=config.get("batch_size", settings.TRAINING_DEFAULT_BATCH_SIZE),
            )

            # 5. Evaluate
            job.progress = 80
            session.commit()

            eval_metrics = trainer.evaluate(test_data)
            metrics.update(eval_metrics)
            trainer.save_adapter(output_dir)

            # 6. Deploy
            job.progress = 90
            session.commit()

            model_name = f"lora-{job_id[:8]}"
            deploy_target_key = config.get("deploy_target_key")
            if deploy_target_key:
                try:
                    from ml.training.registry import get_deployer
                    DeployerClass = get_deployer(deploy_target_key)
                    deployer = DeployerClass()
                    deploy_kwargs = config.get("deploy_config", {})
                    deploy_kwargs["system_prompt"] = deploy_kwargs.get(
                        "system_prompt", settings.TRAINING_SYSTEM_PROMPT
                    )
                    deployer.deploy(
                        model_path=output_dir,
                        model_name=model_name,
                        **deploy_kwargs,
                    )
                    job.deployed_to_target = True
                except Exception as deploy_err:
                    logger.warning(f"Deploy failed (training still succeeded): {deploy_err}")
                    job.deployed_to_target = False

            # 7. Complete
            job.progress = 100
            job.status = "completed"
            job.metrics = metrics
            job.model_name = model_name
            job.completed_at = datetime.now(timezone.utc)
            session.commit()

        except Exception as e:
            logger.error(f"Training job {job_id} failed: {e}")
            job.status = "failed"
            job.error = str(e)
            session.commit()
