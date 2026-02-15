from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import Integer, String, TIMESTAMP, ForeignKey, Float, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, TEXT, JSONB

from app.db.base_class import Base


class TrainingJob(Base):
    __tablename__ = "training_jobs"

    id: Mapped[uuid4] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[uuid4] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[Optional[uuid4]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Catalog references (nullable — allows free-form usage without catalog)
    method_id: Mapped[Optional[uuid4]] = mapped_column(ForeignKey("training_methods.id", ondelete="SET NULL"), nullable=True)
    base_model_id: Mapped[Optional[uuid4]] = mapped_column(ForeignKey("base_model_catalog.id", ondelete="SET NULL"), nullable=True)
    deployment_target_id: Mapped[Optional[uuid4]] = mapped_column(ForeignKey("deployment_targets.id", ondelete="SET NULL"), nullable=True)

    # Resolved values (denormalized for history — catalog entries may change later)
    base_model_name: Mapped[str] = mapped_column(String(255), nullable=False)
    method_key: Mapped[str] = mapped_column(String(50), nullable=False, default="lora")
    config: Mapped[dict] = mapped_column(JSONB, default={}, nullable=False)  # merged training params

    # Job lifecycle
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="queued", index=True)
    progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status_message: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    error: Mapped[Optional[str]] = mapped_column(TEXT, nullable=True)

    # Results
    metrics: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    model_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # output model name
    device_info: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    deployed_to_target: Mapped[Optional[bool]] = mapped_column(default=None, nullable=True)

    # Timestamps
    started_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    tenant: Mapped["Tenant"] = relationship()
    user: Mapped[Optional["User"]] = relationship()
    method: Mapped[Optional["TrainingMethod"]] = relationship()
    base_model: Mapped[Optional["BaseModelCatalog"]] = relationship()
    deployment_target: Mapped[Optional["DeploymentTarget"]] = relationship()
